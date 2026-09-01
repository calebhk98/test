import type { Ctx } from '../lib/ctx.js';
import { NotImplementedError } from '../lib/errors.js';
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

export async function listActiveVenues(ctx: Ctx, params?: { category?: VenueCategory }): Promise<Venue[]> {
  throw new NotImplementedError('venue.listActiveVenues');
}

export async function getVenue(ctx: Ctx, venueId: string): Promise<Venue> {
  throw new NotImplementedError('venue.getVenue');
}

/** Available slots for `venueId` within `[fromDate, toDate)`, derived from `time_slot_config` (spec §13.2 "available time slots") minus already-booked `date_proposals`. */
export async function listAvailableTimeSlots(ctx: Ctx, venueId: string, fromDate: Date, toDate: Date): Promise<VenueTimeSlot[]> {
  throw new NotImplementedError('venue.listAvailableTimeSlots');
}

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

export async function adminListVenues(ctx: Ctx): Promise<Venue[]> {
  throw new NotImplementedError('venue.adminListVenues');
}

export async function adminCreateVenue(ctx: Ctx, input: CreateVenueInput): Promise<Venue> {
  throw new NotImplementedError('venue.adminCreateVenue');
}

export async function adminUpdateVenue(ctx: Ctx, venueId: string, patch: Partial<CreateVenueInput> & { active?: boolean }): Promise<Venue> {
  throw new NotImplementedError('venue.adminUpdateVenue');
}
