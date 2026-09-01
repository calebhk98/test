/**
 * src/http/auth.ts, the auth middleware: turns a bearer access token into
 * a fully-formed `Ctx` (with the correct `Actor`), and the role guards that
 * enforce the three-role boundary (§4) on top of it.
 *
 * ROLE RESOLUTION: `auth.service#login`/`register` (owned by Agent A, not
 * modified here) issue tokens for `users` rows only, there is no
 * "role"-flavored token. A token's bearer's role is instead resolved fresh
 * on every request by checking the `admin_users`/`venue_staff` tables
 * (§4.2/§4.3, "venue staff are users with elevated, venue-scoped access"),
 * admin taking precedence over venue-staff over plain user. This is
 * deliberate: it means revoking an admin's admin-ness (setting
 * `admin_users.active = false`) takes effect on their very next request,
 * with no token invalidation dance required.
 */
import type { FastifyReply, FastifyRequest } from 'fastify';
import * as authService from '../services/auth.service.js';
import { ForbiddenError, UnauthorizedError } from '../lib/errors.js';
import type { Actor, Ctx } from '../lib/ctx.js';
import type { TrustLevel } from '../domain/types.js';
import { ctxWithActor, systemCtx } from './deps.js';
import type { AppDeps } from './deps.js';

declare module 'fastify' {
  interface FastifyRequest {
    /** Populated by `authenticate()` once the bearer token has been verified and the caller's role resolved. Undefined on public routes. */
    ctx?: Ctx;
  }
}

/** Resolves the `Actor` for an authenticated `userId`, see module doc for precedence. */
export async function resolveActor(deps: AppDeps, userId: string): Promise<Actor> {
  const { rows: adminRows } = await deps.pool.query<{ id: string }>(
    `SELECT id FROM admin_users WHERE user_id = $1 AND active = true LIMIT 1`,
    [userId],
  );
  if (adminRows[0]) {
    // `adminId` is deliberately the underlying `users.id`, not
    // `admin_users.id`, `admin_audit_log.admin_user_id` (schema in
    // db/migrations/001_init.sql) is a FK to `users(id)`, so this is the
    // value every audit-log write (`src/http/audit.ts`) needs.
    return { type: 'admin', adminId: userId };
  }

  const { rows: staffRows } = await deps.pool.query<{ id: string; venue_id: string }>(
    `SELECT id, venue_id FROM venue_staff WHERE user_id = $1 AND active = true ORDER BY created_at ASC LIMIT 1`,
    [userId],
  );
  if (staffRows[0]) {
    return { type: 'venue_staff', venueStaffId: staffRows[0].id, venueId: staffRows[0].venue_id };
  }

  const { rows: userRows } = await deps.pool.query<{ trust_level: TrustLevel }>(
    `SELECT trust_level FROM users WHERE id = $1`,
    [userId],
  );
  const trustLevel = userRows[0]?.trust_level ?? 'standard';
  return { type: 'user', userId, trustLevel };
}

function extractBearerToken(req: FastifyRequest): string {
  const header = req.headers.authorization;
  if (!header || Array.isArray(header) || !header.startsWith('Bearer ')) {
    throw new UnauthorizedError('Missing or malformed Authorization header.');
  }
  const token = header.slice('Bearer '.length).trim();
  if (!token) throw new UnauthorizedError('Missing bearer token.');
  return token;
}

/** Fastify preHandler factory: verifies the bearer access token and attaches `req.ctx` (with the resolved-role Actor) for downstream handlers. Every non-public route must run this. */
export function authenticate(deps: AppDeps) {
  return async (req: FastifyRequest, _reply: FastifyReply): Promise<void> => {
    const token = extractBearerToken(req);
    const { userId } = await authService.verifyAccessToken(systemCtx(deps, 'http.auth'), token);
    const actor = await resolveActor(deps, userId);
    req.ctx = ctxWithActor(deps, actor);
  };
}

/** Fastify preHandler factory: 403s unless `req.ctx.actor.type` is one of `allowed`. Always run AFTER `authenticate()`. */
export function requireRole(...allowed: Array<Actor['type']>) {
  return async (req: FastifyRequest, _reply: FastifyReply): Promise<void> => {
    if (!req.ctx) {
      // Programmer error (route wired requireRole without authenticate),
      // fail safe as unauthorized rather than silently allowing through.
      throw new UnauthorizedError('Not authenticated.');
    }
    if (!allowed.includes(req.ctx.actor.type)) {
      throw new ForbiddenError(`This action requires one of [${allowed.join(', ')}].`);
    }
  };
}
