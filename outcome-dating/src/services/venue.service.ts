import { z } from 'zod';
import type { Ctx } from '../lib/ctx.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../lib/errors.js';
import type { Venue, VenueCategory, VenueTimeSlot } from '../domain/types.js';

/**
 * venue.service — the venue directory.
 * Spec: §13.2, §24.8 (`GET /venues`), §27 (admin venue manager).
 *
 * Owning agent: D.
 *
 * Invariants:
 *  - `category` is restricted to the exact §13.2 list at the DB layer
 *    (CHECK constraint) and the type layer (`VenueCategory` union) —
 *    admins can only add venues in these categories in MVP; a "new venue
 *    categories" expansion is feature-flagged (spec §22) and would extend
 *    both, not bypass either.
 *  - `adminUpdateVenue({ active: false })` (spec §30.6 "venue closes")
 *    must not be blocked by existing `date_proposals` referencing the
 *    venue — deactivation only affects future proposal creation
 *    (`dateProposal.service#proposeDate` must reject `venueId`s for
 *    inactive venues); it does not cancel existing tickets. Refund/
 *    reschedule for already-ticketed dates at a since-closed venue is
 *    `dateProposal.service.ts`'s call, not this module's.
 */

const VENUE_CATEGORIES = [
  'coffee',
  'dessert',
  'drinks',
  'walk',
  'museum',
  'arcade',
  'live_music',
  'comedy',
  'class_activity',
  'food_market',
] as const satisfies readonly VenueCategory[];

const REDEMPTION_METHODS = ['qr_scan', 'manual_code'] as const;

const TimeSlotSchema = z.object({
  dayOfWeek: z.number().int().min(0).max(6),
  startMinute: z.number().int().min(0).max(24 * 60),
  endMinute: z.number().int().min(0).max(24 * 60),
}).refine((s) => s.endMinute > s.startMinute, { message: 'endMinute must be after startMinute' });

const CreateVenueSchema = z.object({
  name: z.string().min(1).max(200),
  address: z.string().min(1).max(400),
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  category: z.enum(VENUE_CATEGORIES),
  marginPercent: z.number().min(0).max(100),
  timeSlots: z.array(TimeSlotSchema),
  redemptionMethod: z.enum(REDEMPTION_METHODS),
});

export interface CreateVenueInput {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  category: VenueCategory;
  marginPercent: number;
  timeSlots: VenueTimeSlot[];
  redemptionMethod: 'qr_scan' | 'manual_code';
}

function requireAdminActor(ctx: Ctx): void {
  if (ctx.actor.type !== 'admin') throw new ForbiddenError('Admin actor required');
}

interface VenueRow {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  category: VenueCategory;
  active: boolean;
  margin_percent: number;
  time_slot_config: unknown;
  redemption_method: 'qr_scan' | 'manual_code';
  created_at: Date;
}

/** `time_slot_config` is stored as `{ slots: VenueTimeSlot[] }` (see `src/seed.ts` for the same shape). */
function extractTimeSlots(config: unknown): VenueTimeSlot[] {
  if (config && typeof config === 'object' && Array.isArray((config as { slots?: unknown }).slots)) {
    return (config as { slots: VenueTimeSlot[] }).slots;
  }
  return [];
}

function mapVenue(row: VenueRow): Venue {
  return {
    id: row.id,
    name: row.name,
    address: row.address,
    latitude: Number(row.latitude),
    longitude: Number(row.longitude),
    category: row.category,
    active: row.active,
    marginPercent: Number(row.margin_percent),
    timeSlots: extractTimeSlots(row.time_slot_config),
    redemptionMethod: row.redemption_method,
    createdAt: row.created_at,
  };
}

export async function listActiveVenues(ctx: Ctx, params?: { category?: VenueCategory }): Promise<Venue[]> {
  const conditions = ['active = true'];
  const values: unknown[] = [];
  if (params?.category) {
    values.push(params.category);
    conditions.push(`category = $${values.length}`);
  }
  const { rows } = await ctx.db.query<VenueRow>(`SELECT * FROM venues WHERE ${conditions.join(' AND ')} ORDER BY name`, values);
  return rows.map(mapVenue);
}

export async function getVenue(ctx: Ctx, venueId: string): Promise<Venue> {
  if (!z.string().uuid().safeParse(venueId).success) throw new ValidationError('venueId must be a uuid');
  const { rows } = await ctx.db.query<VenueRow>(`SELECT * FROM venues WHERE id = $1`, [venueId]);
  if (!rows[0]) throw new NotFoundError('Venue not found');
  return mapVenue(rows[0]);
}

/**
 * Available slots for `venueId` within `[fromDate, toDate)`, derived from
 * `time_slot_config` (spec §13.2 "available time slots") minus already-
 * booked `date_proposals`.
 *
 * SIMPLIFICATION (documented, not hidden): a `VenueTimeSlot` is a
 * *recurring weekly* window (day-of-week + minute-of-day range), while a
 * booking is one concrete `scheduled_start`/`scheduled_end`. Rather than
 * enumerate every weekly occurrence in the range and check each one
 * individually (real capacity planning, out of scope for this MVP layer),
 * a recurring slot is considered unavailable for the whole `[fromDate,
 * toDate)` window as soon as ANY non-terminal booking exists whose
 * `scheduled_start` falls on that slot's day-of-week and inside its
 * minute-of-day range. This is conservative (may hide a slot that still
 * has some free weeks) but never double-books.
 */
const SLOT_BLOCKING_STATUSES = ['pending_acceptance', 'accepted', 'charged', 'ticketed', 'completed', 'completed_unverified'] as const;

export async function listAvailableTimeSlots(ctx: Ctx, venueId: string, fromDate: Date, toDate: Date): Promise<VenueTimeSlot[]> {
  const venue = await getVenue(ctx, venueId);
  if (!venue.active) return [];
  if (venue.timeSlots.length === 0) return [];

  const { rows: bookings } = await ctx.db.query<{ scheduled_start: Date }>(
    `SELECT scheduled_start FROM date_proposals
     WHERE venue_id = $1 AND scheduled_start >= $2 AND scheduled_start < $3
       AND status = ANY($4::text[])`,
    [venueId, fromDate, toDate, SLOT_BLOCKING_STATUSES as unknown as string[]],
  );

  return venue.timeSlots.filter((slot) => {
    return !bookings.some((b) => {
      const start = b.scheduled_start;
      const dayOfWeek = start.getUTCDay();
      const minuteOfDay = start.getUTCHours() * 60 + start.getUTCMinutes();
      return dayOfWeek === slot.dayOfWeek && minuteOfDay >= slot.startMinute && minuteOfDay < slot.endMinute;
    });
  });
}

export async function adminListVenues(ctx: Ctx): Promise<Venue[]> {
  requireAdminActor(ctx);
  const { rows } = await ctx.db.query<VenueRow>(`SELECT * FROM venues ORDER BY name`);
  return rows.map(mapVenue);
}

export async function adminCreateVenue(ctx: Ctx, input: CreateVenueInput): Promise<Venue> {
  requireAdminActor(ctx);
  const parsed = CreateVenueSchema.parse(input);

  const { rows } = await ctx.db.query<VenueRow>(
    `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
     VALUES ($1, $2, $3, $4, $5, true, $6, $7::jsonb, $8)
     RETURNING *`,
    [
      parsed.name,
      parsed.address,
      parsed.latitude,
      parsed.longitude,
      parsed.category,
      parsed.marginPercent,
      JSON.stringify({ slots: parsed.timeSlots }),
      parsed.redemptionMethod,
    ],
  );
  return mapVenue(rows[0]!);
}

const UpdateVenueSchema = CreateVenueSchema.partial().extend({ active: z.boolean().optional() });

export async function adminUpdateVenue(ctx: Ctx, venueId: string, patch: Partial<CreateVenueInput> & { active?: boolean }): Promise<Venue> {
  requireAdminActor(ctx);
  if (!z.string().uuid().safeParse(venueId).success) throw new ValidationError('venueId must be a uuid');
  const parsed = UpdateVenueSchema.parse(patch);

  const sets: string[] = [];
  const values: unknown[] = [];
  const push = (col: string, value: unknown, cast = '') => {
    values.push(value);
    sets.push(`${col} = $${values.length}${cast}`);
  };

  if (parsed.name !== undefined) push('name', parsed.name);
  if (parsed.address !== undefined) push('address', parsed.address);
  if (parsed.latitude !== undefined) push('latitude', parsed.latitude);
  if (parsed.longitude !== undefined) push('longitude', parsed.longitude);
  if (parsed.category !== undefined) push('category', parsed.category);
  if (parsed.marginPercent !== undefined) push('margin_percent', parsed.marginPercent);
  if (parsed.timeSlots !== undefined) push('time_slot_config', JSON.stringify({ slots: parsed.timeSlots }), '::jsonb');
  if (parsed.redemptionMethod !== undefined) push('redemption_method', parsed.redemptionMethod);
  if (parsed.active !== undefined) push('active', parsed.active);

  if (sets.length === 0) return getVenue(ctx, venueId);

  values.push(venueId);
  const { rows } = await ctx.db.query<VenueRow>(
    `UPDATE venues SET ${sets.join(', ')} WHERE id = $${values.length} RETURNING *`,
    values,
  );
  if (!rows[0]) throw new NotFoundError('Venue not found');
  return mapVenue(rows[0]);
}
