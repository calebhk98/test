/**
 * src/http/middleware/locale.ts, per-request locale resolution.
 *
 * `src/domain/i18n/locales.ts#resolveLocale` already implements the
 * negotiation rule (a stored preference always wins over the request's
 * `Accept-Language` header, see that function's own doc), and
 * `i18n.routes.ts` already reads the caller's stored preference inline for
 * `GET /me/locale`. This module is that exact same two-step lookup
 * (`user_locale_preferences` row, then `resolveLocale`), factored out so
 * every OTHER route that wants to honour a caller's negotiated locale
 * (starting with the questions routes, see `questions.routes.ts`) doesn't
 * have to re-open-code the query.
 */
import type { FastifyRequest } from 'fastify';
import type { Ctx } from '../../lib/ctx.js';
import { requireUserActor } from '../../lib/ctx.js';
import { resolveLocale } from '../../domain/i18n/locales.js';
import type { LocaleTag } from '../../domain/i18n/locales.js';

export function acceptLanguageHeader(req: FastifyRequest): string | undefined {
  const header = req.headers['accept-language'];
  if (Array.isArray(header)) return header[0];
  return header;
}

/**
 * Resolves the caller's negotiated locale: their stored preference
 * (`user_locale_preferences`) if one exists, otherwise their request's
 * `Accept-Language` header, otherwise the platform default (`en`). Requires
 * an authenticated user actor (same guard every `/me/*` route already
 * runs), a route with no `req.ctx` yet has nothing to resolve a stored
 * preference against.
 */
export async function resolveRequestLocale(ctx: Ctx, req: FastifyRequest): Promise<LocaleTag> {
  const { userId } = requireUserActor(ctx);
  const { rows } = await ctx.db.query<{ locale: string }>(
    `SELECT locale FROM user_locale_preferences WHERE user_id = $1`,
    [userId],
  );
  const resolved = resolveLocale({ storedPreference: rows[0]?.locale ?? null, acceptLanguageHeader: acceptLanguageHeader(req) });
  return resolved.locale;
}
