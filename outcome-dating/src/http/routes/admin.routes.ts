/**
 * §24.13 Admin routes, plus the handful of additions needed to actually
 * back every §27 admin-panel capability with a real endpoint (flagged
 * individually below and in `src/http/routeTable.ts`).
 *
 * EVERY MUTATING ROUTE HERE CALLS `writeAdminAudit` AFTER THE UNDERLYING
 * SERVICE CALL SUCCEEDS (spec §4.3, §28.6, C-28.6.1) — this is the
 * enforcement point for "every admin mutation writes admin_audit_log" from
 * the task brief. Read-only routes do not (nothing changed to audit).
 *
 * Admin is NEVER required for moderation to function (spec §18.1) — no
 * route in this file is on the moderation pipeline's own call path
 * (`report.submitReport` → `moderation.recordAutomatedFlag` →
 * `moderation.applyThresholds` all run without any admin involvement, see
 * `report.service.ts`); `GET /admin/moderation/actions` is read-only
 * observability, not a step the pipeline depends on.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as questionService from '../../services/question.service.js';
import * as venueService from '../../services/venue.service.js';
import * as moderationService from '../../services/moderation.service.js';
import * as ledgerService from '../../services/ledger.service.js';
import * as paymentService from '../../services/payment.service.js';
import * as dateProposalService from '../../services/dateProposal.service.js';
import { ConfigKeyRegistry } from '../../config/config.service.js';
import type { ConfigKey } from '../../config/config.service.js';
import { NotFoundError, ValidationError } from '../../lib/errors.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { writeAdminAudit } from '../audit.js';
import { paginationQuerySchema, parseOrThrow, requireUuidParam } from '../validation.js';
import { serializeAdminQuestion } from '../serializers/questions.js';

const VenueCategorySchema = z.enum([
  'coffee', 'dessert', 'drinks', 'walk', 'museum', 'arcade', 'live_music', 'comedy', 'class_activity', 'food_market',
]);
const TimeSlotSchema = z.object({ dayOfWeek: z.number(), startMinute: z.number(), endMinute: z.number() });
const CreateVenueBodySchema = z.object({
  name: z.string(),
  address: z.string(),
  latitude: z.number(),
  longitude: z.number(),
  category: VenueCategorySchema,
  marginPercent: z.number(),
  timeSlots: z.array(TimeSlotSchema),
  redemptionMethod: z.enum(['qr_scan', 'manual_code']),
});
const UpdateVenueBodySchema = CreateVenueBodySchema.partial().extend({ active: z.boolean().optional() });

// §27 item 3 (question manager) body shapes: src/services/question.service.ts
// `CreateQuestionBankInput` / `UpdateQuestionBankInput` — the ONE typed
// question bank (question_bank/user_question_answers) per the
// question-system cutover (see that file's file-level CUTOVER doc). Full
// shape validation (including the discriminated-union `typeDef` per
// question type, and the "no section mark in user-visible text" guard) is
// the SERVICE's job, not this route layer's — same "route layer only
// handles params/query, the service validates the body" pattern
// `src/http/routes/questions.routes.ts` already uses for `PUT /me/answers`.
const ListQuestionBankQuerySchema = z.object({ includeInactive: z.coerce.boolean().optional() });

const SetConfigBodySchema = z.object({ key: z.string(), value: z.unknown() });
const SetFlagBodySchema = z.object({
  key: z.string(),
  enabled: z.boolean().optional(),
  rolloutPercent: z.number().min(0).max(100).optional(),
  segments: z.array(z.string()).optional(),
});
const RefundHoldBodySchema = z.object({ amountCents: z.number().int().min(0).optional(), reason: z.string().optional() });
const UsersQuerySchema = z.object({ q: z.string().optional(), limit: z.coerce.number().int().min(1).max(200).optional() });

function isConfigKey(key: string): key is ConfigKey {
  return Object.prototype.hasOwnProperty.call(ConfigKeyRegistry, key);
}

export function registerAdminRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('admin')] };

  // ---- §27 item 1: Config editor ----
  app.get('/admin/config', auth, async (req, reply) => {
    const keys = Object.keys(ConfigKeyRegistry) as ConfigKey[];
    const entries = await Promise.all(
      keys.map(async (key) => ({
        key,
        value: await req.ctx!.config.get(key),
        scope: ConfigKeyRegistry[key].scope,
        description: ConfigKeyRegistry[key].description,
        specSection: ConfigKeyRegistry[key].specSection,
      })),
    );
    reply.send(entries);
  });

  app.patch('/admin/config', auth, async (req, reply) => {
    const body = parseOrThrow(SetConfigBodySchema, req.body);
    if (!isConfigKey(body.key)) throw new ValidationError(`Unknown config key "${body.key}".`, { key: body.key });
    const before = await req.ctx!.config.get(body.key);
    await req.ctx!.config.set(body.key, body.value as never, req.ctx!.actor.type === 'admin' ? req.ctx!.actor.adminId : 'admin');
    const after = await req.ctx!.config.get(body.key);
    await writeAdminAudit(req.ctx!, { action: 'config.set', targetType: 'config_entries', targetId: body.key, before, after });
    reply.send({ key: body.key, value: after });
  });

  // ---- §27 item 2: Feature flag manager ----
  app.get('/admin/feature-flags', auth, async (req, reply) => {
    reply.send(await req.ctx!.flags.listFlags());
  });

  app.post('/admin/feature-flags', auth, async (req, reply) => {
    const body = parseOrThrow(SetFlagBodySchema, req.body);
    const before = await req.ctx!.flags.getFlag(body.key);
    const after = await req.ctx!.flags.setFlag(body.key, body);
    await writeAdminAudit(req.ctx!, { action: 'feature_flag.set', targetType: 'feature_flags', targetId: body.key, before, after });
    reply.send(after);
  });

  // ---- §27 item 3: Question manager ----
  //
  // Repointed to the ONE typed question bank (`question_bank`/
  // `user_question_answers`, db/migrations/008_questions.sql) — this used
  // to create/edit rows in the OLD `questions` table, which the product
  // never scores or shows to a user answering `GET /questions`; an admin
  // using the old panel could recreate the exact "asked about the same
  // concept through two different definitions" duplication the product
  // owner flagged (children/religion asked 3-4 times by a prior team).
  // See src/services/question.service.ts's file-level CUTOVER doc for the
  // full accounting of what moved.
  //
  // `:id` in the PATCH path is kept literally (not renamed `:slug`) only
  // because `tests/http/routeTable.test.ts` (frozen, not owned by this
  // build) hardcodes the exact path string `/admin/questions/:id` — the
  // typed bank's admin update is actually keyed by SLUG (editing inserts a
  // new version rather than mutating in place, see
  // `question.service#adminUpdateQuestionBankEntry`'s doc), so the value
  // carried by that param is a slug, not a uuid.
  app.get('/admin/questions', auth, async (req, reply) => {
    const query = parseOrThrow(ListQuestionBankQuerySchema, req.query);
    // Admins managing the bank need to see inactive/retired questions too
    // (to review or reactivate them), not just what's currently offered to
    // users — default to the full bank unless the caller asks to narrow it.
    const items = await questionService.adminListQuestionBank(req.ctx!, {
      includeInactive: query.includeInactive ?? true,
    });
    reply.send(items.map(serializeAdminQuestion));
  });

  app.post('/admin/questions', auth, async (req, reply) => {
    const created = await questionService.adminCreateQuestionBankEntry(
      req.ctx!,
      req.body as questionService.CreateQuestionBankInput,
    );
    await writeAdminAudit(req.ctx!, {
      action: 'question.create',
      targetType: 'question_bank',
      targetId: created.id,
      after: created,
    });
    reply.status(201).send(serializeAdminQuestion(created));
  });

  app.patch('/admin/questions/:id', auth, async (req, reply) => {
    const slug = parseOrThrow(z.string().min(1), (req.params as Record<string, unknown> | null | undefined)?.id);
    const updated = await questionService.adminUpdateQuestionBankEntry(
      req.ctx!,
      slug,
      req.body as questionService.UpdateQuestionBankInput,
    );
    await writeAdminAudit(req.ctx!, {
      action: 'question.update',
      targetType: 'question_bank',
      targetId: updated.id,
      after: updated,
    });
    reply.send(serializeAdminQuestion(updated));
  });

  // ---- §27 item 4: Venue manager ----
  app.get('/admin/venues', auth, async (req, reply) => {
    reply.send(await venueService.adminListVenues(req.ctx!));
  });

  app.post('/admin/venues', auth, async (req, reply) => {
    const body = parseOrThrow(CreateVenueBodySchema, req.body);
    const created = await venueService.adminCreateVenue(req.ctx!, body);
    await writeAdminAudit(req.ctx!, { action: 'venue.create', targetType: 'venues', targetId: created.id, after: created });
    reply.status(201).send(created);
  });

  // Addition — conformance C-30.6.1 explicitly requires this route ("admin
  // marks a venue inactive after it closes"); §24.13's literal list omits
  // it but §27 item 4 ("venue manager") implies update capability.
  app.patch('/admin/venues/:id', auth, async (req, reply) => {
    const id = requireUuidParam(req.params, 'id');
    const body = parseOrThrow(UpdateVenueBodySchema, req.body);
    const before = await venueService.getVenue(req.ctx!, id);
    const updated = await venueService.adminUpdateVenue(req.ctx!, id, body);
    await writeAdminAudit(req.ctx!, { action: 'venue.update', targetType: 'venues', targetId: id, before, after: updated });
    reply.send(updated);
  });

  // ---- §27 item 5: User lookup ----
  app.get('/admin/users', auth, async (req, reply) => {
    const query = parseOrThrow(UsersQuerySchema, req.query);
    const limit = query.limit ?? 50;
    const { rows } = query.q
      ? await req.ctx!.db.query(
          `SELECT id, email, status, trust_score, trust_level, shadowbanned, suspended, created_at, last_active_at
           FROM users WHERE email ILIKE $1 ORDER BY created_at DESC LIMIT $2`,
          [`%${query.q}%`, limit],
        )
      : await req.ctx!.db.query(
          `SELECT id, email, status, trust_score, trust_level, shadowbanned, suspended, created_at, last_active_at
           FROM users ORDER BY created_at DESC LIMIT $1`,
          [limit],
        );
    reply.send(rows);
  });

  app.get('/admin/users/:userId', auth, async (req, reply) => {
    const userId = requireUuidParam(req.params, 'userId');
    const { rows } = await req.ctx!.db.query(
      `SELECT id, email, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at, created_at, last_active_at
       FROM users WHERE id = $1`,
      [userId],
    );
    if (!rows[0]) throw new NotFoundError('User not found.');
    reply.send(rows[0]);
  });

  // ---- §27 item 6: Trust event viewer ----
  app.get('/admin/users/:userId/trust-events', auth, async (req, reply) => {
    const userId = requireUuidParam(req.params, 'userId');
    const query = parseOrThrow(paginationQuerySchema, req.query);
    const limit = Math.min(200, Math.max(1, query.limit ?? 50));
    const offset = query.cursor ? Number(query.cursor) : 0;
    const { rows } = await req.ctx!.db.query(
      `SELECT id, user_id, event_type, delta, metadata, created_at FROM trust_events
       WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3`,
      [userId, limit, offset],
    );
    reply.send(rows);
  });

  // ---- §27 item 7: Moderation action viewer ----
  app.get('/admin/moderation/actions', auth, async (req, reply) => {
    const q = req.query as { userId?: string } & Record<string, unknown>;
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(await moderationService.listModerationActions(req.ctx!, q.userId, query));
  });

  // ---- §27 item 8: Payment ledger viewer ----
  app.get('/admin/users/:userId/ledger', auth, async (req, reply) => {
    const userId = requireUuidParam(req.params, 'userId');
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(await ledgerService.listEntriesForUser(req.ctx!, userId, query));
  });

  // §4.3.6 addition: admin-only, logged dispute-override path (refund or
  // release a specific hold outside the normal cancellation flow) — "only
  // where legally necessary", gated to admin and audited.
  app.post('/admin/payment-holds/:paymentHoldId/refund', auth, async (req, reply) => {
    const paymentHoldId = requireUuidParam(req.params, 'paymentHoldId');
    const body = parseOrThrow(RefundHoldBodySchema, req.body);
    const result = await paymentService.refundHold(req.ctx!, paymentHoldId, body.amountCents);
    await writeAdminAudit(req.ctx!, {
      action: 'payment_hold.dispute_override_refund',
      targetType: 'payment_holds',
      targetId: paymentHoldId,
      after: { status: result.status, reason: body.reason },
    });
    reply.send(result);
  });

  // §30.6.2 addition: admin cancels/refunds a ticketed proposal whose venue
  // went inactive before the scheduled time (operational failure must not
  // punish users).
  app.post('/admin/date-proposals/:dateProposalId/cancel', auth, async (req, reply) => {
    const dateProposalId = requireUuidParam(req.params, 'dateProposalId');
    const result = await dateProposalService.cancelDateProposal(req.ctx!, dateProposalId);
    await writeAdminAudit(req.ctx!, {
      action: 'date_proposal.admin_cancel',
      targetType: 'date_proposals',
      targetId: dateProposalId,
      after: { status: result.status },
    });
    reply.send(result);
  });

  // ---- §27 items 9-12 + §26: analytics/funnel/report-trend/date-completion/photo-AB, folded into one overview endpoint ----
  app.get('/admin/analytics/overview', auth, async (req, reply) => {
    reply.send(await buildAnalyticsOverview(req.ctx!));
  });
}

async function scalarCount(ctx: import('../../lib/ctx.js').Ctx, sql: string, params: unknown[] = []): Promise<number> {
  const { rows } = await ctx.db.query<{ count: string }>(sql, params);
  return Number(rows[0]?.count ?? 0);
}

/**
 * §26.1/§26.2 core + quality metrics, plus the §27 report-trend/
 * date-completion/photo-A/B/funnel views folded into one response —
 * documented in `routeTable.ts` as covering those four §27 items via this
 * one endpoint rather than four near-identical new routes. Never reachable
 * by a non-admin actor (C-26.3) — this function is only ever called from
 * the admin-gated route above.
 */
async function buildAnalyticsOverview(ctx: import('../../lib/ctx.js').Ctx): Promise<Record<string, unknown>> {
  const [
    registrations,
    verifiedEmails,
    profilesCompleted,
    discoveryImpressions,
    interestsSent,
    interestsAccepted,
    conversationsOpened,
    dateProposalsSent,
    dateProposalsAccepted,
    datesCompleted,
    voucherRedemptions,
    refunds,
    noShows,
    reportsCount,
    blocksCount,
    shadowbans,
  ] = await Promise.all([
    scalarCount(ctx, `SELECT count(*)::text AS count FROM users`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM users WHERE email_verified_at IS NOT NULL`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM profiles WHERE profile_completeness >= 100`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM discovery_events`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM interests`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM interests WHERE status = 'accepted'`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM conversations`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM date_proposals`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM date_proposals WHERE status NOT IN ('draft','pending_acceptance','payment_failed')`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM date_proposals WHERE status IN ('completed','completed_unverified')`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM venue_redemptions`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM payment_ledger WHERE type = 'refund'`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM date_proposals WHERE status = 'no_show'`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM reports`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM blocks`),
    scalarCount(ctx, `SELECT count(*)::text AS count FROM users WHERE shadowbanned = true`),
  ]);

  const [{ rows: reportsByCategory }, { rows: photoRecommendations }] = await Promise.all([
    ctx.db.query<{ category: string; count: string }>(
      `SELECT category, count(*)::text AS count FROM reports GROUP BY category ORDER BY count(*) DESC`,
    ),
    ctx.db.query<{ status: string; count: string }>(
      `SELECT status, count(*)::text AS count FROM photo_recommendations GROUP BY status`,
    ),
  ]);

  const dateCompletionDenominator = await scalarCount(
    ctx,
    `SELECT count(*)::text AS count FROM date_proposals WHERE status IN ('completed','completed_unverified','no_show','disputed','refunded','canceled')`,
  );

  return {
    coreMetrics: {
      registrations,
      verifiedEmails,
      profilesCompleted,
      discoveryImpressions,
      interestsSent,
      interestsAccepted,
      conversationsOpened,
      dateProposalsSent,
      dateProposalsAccepted,
      datesCompleted,
      voucherRedemptions,
      refunds,
      noShows,
      reports: reportsCount,
      blocks: blocksCount,
      shadowbans,
    },
    qualityMetrics: {
      acceptedInterestRate: interestsSent > 0 ? interestsAccepted / interestsSent : 0,
      dateCompletionRate: dateCompletionDenominator > 0 ? datesCompleted / dateCompletionDenominator : 0,
      noShowRate: dateCompletionDenominator > 0 ? noShows / dateCompletionDenominator : 0,
      chatToDateConversionRate: conversationsOpened > 0 ? dateProposalsSent / conversationsOpened : 0,
    },
    // §27 item 9: report trend dashboard.
    reportTrends: { byCategory: reportsByCategory },
    // §27 item 10: date completion dashboard.
    dateCompletion: { completed: datesCompleted, denominator: dateCompletionDenominator },
    // §27 item 11: photo A/B results.
    photoAbResults: { recommendationsByStatus: photoRecommendations },
    // §27 item 12: funnel analytics (registration -> ... -> completed date).
    funnel: {
      registrations,
      profilesCompleted,
      interestsSent,
      interestsAccepted,
      dateProposalsSent,
      datesCompleted,
    },
  };
}
