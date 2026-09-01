import type { DbClient } from '../db/pool.js';
import type { Clock } from './time.js';
import type { Logger } from './logger.js';
import type { ConfigService } from '../config/config.service.js';
import type { FlagsService } from '../config/flags.service.js';
import type { TrustLevel } from '../domain/types.js';
import type { PaymentProcessor } from '../services/payments/processor.port.js';
import type { ImageModerationPort } from '../services/media/moderation.port.js';
import { ForbiddenError } from './errors.js';

/**
 * Who is performing the current action. Every service function takes this
 * as part of `Ctx` rather than a bare `userId`, because several modules
 * (venue redemption, admin config, background jobs) are called by actors
 * that are not a regular user, and several invariants (e.g. "venue staff
 * cannot see chats") are enforced by checking `actor.type`, not just an id.
 */
export type Actor =
  | { type: 'user'; userId: string; trustLevel: TrustLevel }
  | { type: 'venue_staff'; venueStaffId: string; venueId: string }
  | { type: 'admin'; adminId: string }
  /** Background jobs (spec §25) and the migration/seed scripts run as `system`. */
  | { type: 'system'; job: string };

/**
 * The single context object threaded as the first argument through every
 * service function (see INTERFACES.md). Bundling db/clock/config/flags/
 * logger/actor together, rather than each function taking its own subset
 * of params, is what lets services compose inside one transaction: a
 * caller does `withTransaction(db => fn(withDb(ctx, db)))` and every
 * service invoked with the resulting `Ctx` shares that same transaction.
 *
 * `payments`/`media` are the two external-integration PORTS the spec calls
 * out explicitly (§14 payment processor, §7.2 image moderation), they're
 * threaded through `Ctx` rather than imported as singletons by each
 * service file so that (a) tests can inject `FakeProcessor`/
 * `StubMediaModerationAdapter` per-call with zero module-level mocking,
 * and (b) `dateProposal`/`payment`/`voucher`/`photo` service bodies never
 * need to know which concrete adapter is configured.
 */
export interface Ctx {
  db: DbClient;
  clock: Clock;
  config: ConfigService;
  flags: FlagsService;
  logger: Logger;
  actor: Actor;
  payments: PaymentProcessor;
  media: ImageModerationPort;
}

/** Returns a new Ctx with `db` swapped out, e.g. to bind to a transaction's client. Every other field is shared by reference. */
export function withDb(ctx: Ctx, db: DbClient): Ctx {
  return { ...ctx, db };
}

/** Returns a new Ctx with `actor` swapped out, e.g. a job impersonating "system" calling a user-shaped service function on a user's behalf. */
export function withActor(ctx: Ctx, actor: Actor): Ctx {
  return { ...ctx, actor };
}

/** Throws if the current actor is not an authenticated regular user; otherwise returns their userId. Common guard at the top of user-facing service functions. */
export function requireUserActor(ctx: Ctx): { userId: string; trustLevel: TrustLevel } {
  if (ctx.actor.type !== 'user') {
    throw new ForbiddenError(`Expected a user actor, got "${ctx.actor.type}"`);
  }
  return ctx.actor;
}
