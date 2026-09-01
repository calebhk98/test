/**
 * src/http/routes/i18n.routes.ts, locale discovery + per-user locale
 * preference (task brief: "Locale negotiation per user, honouring a
 * stored preference over a request header").
 *
 * `GET /locales` is public (a client needs to build a language picker
 * before a user is signed in, e.g. on the registration screen).
 * `GET|PUT /me/locale` require a user, same auth shape every other
 * `/me/*` route in this codebase uses (see devices.routes.ts).
 *
 * Storage is a dedicated `user_locale_preferences` table (this build's
 * own migration), not a `users`/`profiles` column, see that migration's
 * own doc for why. Kept inline in this route file rather than a separate
 * service module: two small, single-table queries, no business logic
 * beyond validation, and this build's file list names exactly this one
 * new route file, not an additional service file for it.
 */
import type { FastifyInstance, FastifyRequest } from 'fastify';
import { z } from 'zod';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow } from '../validation.js';
import { LOCALE_REGISTRY, normalizeLocaleTag, resolveLocale } from '../../domain/i18n/locales.js';
import { requireUserActor } from '../../lib/ctx.js';

/**
 * A permissive BCP-47-shaped tag: 2-3 lowercase letters, optionally
 * followed by "-" and a 2-4 alphanumeric region/script subtag (covers
 * every `LOCALE_REGISTRY` entry, "en", "es", "pt-BR", and any future
 * one without a migration/code change). Deliberately not validated
 * against `LOCALE_REGISTRY` itself: storing a preference for a locale
 * this backend hasn't shipped real copy for yet is legal and safe, see
 * translate.ts's fallback chain, a client should not be blocked from
 * recording "the user asked for French" the day France support is only
 * "needs_translation".
 */
const LocaleTagSchema = z
  .string()
  .trim()
  .regex(/^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,4})?$/, 'Must be a BCP-47-shaped locale tag, e.g. "en" or "es-MX".');

const SetLocaleBodySchema = z.object({ locale: LocaleTagSchema });

function acceptLanguageHeader(req: FastifyRequest): string | undefined {
  const header = req.headers['accept-language'];
  if (Array.isArray(header)) return header[0];
  return header;
}

export function registerI18nRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  // Public: a client needs this before a user is signed in (registration
  // screen's own language picker).
  app.get('/locales', async (_req, reply) => {
    reply.send({ locales: LOCALE_REGISTRY, defaultLocale: 'en' });
  });

  app.get('/me/locale', auth, async (req, reply) => {
    const { userId } = requireUserActor(req.ctx!);
    const { rows } = await req.ctx!.db.query<{ locale: string }>(`SELECT locale FROM user_locale_preferences WHERE user_id = $1`, [userId]);
    const resolved = resolveLocale({ storedPreference: rows[0]?.locale ?? null, acceptLanguageHeader: acceptLanguageHeader(req) });
    reply.send(resolved);
  });

  app.put('/me/locale', auth, async (req, reply) => {
    const body = parseOrThrow(SetLocaleBodySchema, req.body);
    const locale = normalizeLocaleTag(body.locale);
    const { userId } = requireUserActor(req.ctx!);
    const now = req.ctx!.clock.now();
    const { rows } = await req.ctx!.db.query<{ locale: string; updated_at: Date }>(
      `INSERT INTO user_locale_preferences (user_id, locale, updated_at)
       VALUES ($1, $2, $3)
       ON CONFLICT (user_id) DO UPDATE SET locale = EXCLUDED.locale, updated_at = EXCLUDED.updated_at
       RETURNING locale, updated_at`,
      [userId, locale, now],
    );
    reply.send({ locale: rows[0]!.locale, updatedAt: rows[0]!.updated_at });
  });
}
