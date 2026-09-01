/**
 * src/http/audit.ts — writes `admin_audit_log` rows (spec §4.3, §21.2,
 * §27, §28.6: "log admin actions" / "log config changes").
 *
 * `admin_audit_log` (schema in `db/migrations/001_init.sql`, "implied —
 * §4.3, §21.2, §27, §28.6") has no owning service module in INTERFACES.md's
 * table — it's an HTTP/admin-panel concern, so it lives here rather than in
 * any `src/services/*` file. Every `/admin/*` route that MUTATES state
 * calls `writeAdminAudit` after the mutation succeeds (never before — an
 * audit row for a write that then fails would be a false record).
 */
import type { Ctx } from '../lib/ctx.js';
import { ForbiddenError } from '../lib/errors.js';

export interface AdminAuditInput {
  /** e.g. "config.set", "question.create", "venue.update", "feature_flag.set" — dot-namespaced, stable across the life of the endpoint. */
  action: string;
  /** e.g. "config_entries", "questions", "venues", "feature_flags", "users", "payment_holds". */
  targetType: string;
  targetId?: string | null;
  before?: unknown;
  after?: unknown;
}

/** Requires `ctx.actor.type === 'admin'` (defense in depth — every call site should already be behind `requireRole('admin')`) and inserts one `admin_audit_log` row. */
export async function writeAdminAudit(ctx: Ctx, input: AdminAuditInput): Promise<void> {
  if (ctx.actor.type !== 'admin') {
    throw new ForbiddenError('Only an admin actor can write an audit log entry.');
  }
  await ctx.db.query(
    `INSERT INTO admin_audit_log (admin_user_id, action, target_type, target_id, before_json, after_json, created_at)
     VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7)`,
    [
      ctx.actor.adminId,
      input.action,
      input.targetType,
      input.targetId ?? null,
      input.before === undefined ? null : JSON.stringify(input.before),
      input.after === undefined ? null : JSON.stringify(input.after),
      ctx.clock.now(),
    ],
  );
}
