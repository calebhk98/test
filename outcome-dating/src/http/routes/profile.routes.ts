/**
 * §24.2 Profile routes, plus the small set of additions flagged in
 * `profile.service.ts`'s own module doc (`deleteMyAccount`/`exportMyData`,
 * §29) and the photo/photo-A/B/behavioral-prompt routes those modules
 * expose (§7.2, §7.3, §17).
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as profileService from '../../services/profile.service.js';
import * as photoService from '../../services/photo.service.js';
import * as photoAltTextService from '../../services/photoAltText.service.js';
import * as photoExperimentService from '../../services/photoExperiment.service.js';
import * as behavioralPromptService from '../../services/behavioralPrompt.service.js';
import { ConflictError, NotFoundError } from '../../lib/errors.js';
import { requireUserActor } from '../../lib/ctx.js';
import type { User } from '../../domain/types.js';
import { BODY_TYPES } from '../../domain/units/bodyType.js';
import { unitPreferenceSchema } from '../../domain/units/preference.js';
import { IMPORTANCE_LEVELS } from '../../domain/questions/index.js';
import { serializeMe } from '../serializers/user.js';
import { serializeMyProfile } from '../serializers/profile.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow, requireUuidParam } from '../validation.js';
import { withIdempotencyKey, idempotencyKeyHeader } from '../middleware/idempotency.js';

interface UserRow {
  id: string;
  email: string;
  password_hash: string;
  birthdate: string;
  status: User['status'];
  trust_score: number;
  trust_level: User['trustLevel'];
  shadowbanned: boolean;
  suspended: boolean;
  email_verified_at: Date | null;
  created_at: Date;
  last_active_at: Date;
}

function mapUserRow(row: UserRow): User {
  return {
    id: row.id,
    email: row.email,
    passwordHash: row.password_hash,
    birthdate: row.birthdate,
    status: row.status,
    trustScore: row.trust_score,
    trustLevel: row.trust_level,
    shadowbanned: row.shadowbanned,
    suspended: row.suspended,
    emailVerifiedAt: row.email_verified_at,
    createdAt: row.created_at,
    lastActiveAt: row.last_active_at,
  };
}

const PatchMeSchema = z.object({ email: z.string().trim().email().max(320).optional() });
const UpdateProfileBodySchema = z.object({
  displayName: z.string().optional(),
  bio: z.string().optional(),
  city: z.string().optional(),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  age: z.number().optional(),
  gender: z.string().optional(),
  seeking: z.string().optional(),
  relationshipIntention: z.string().optional(),
  // These six were accepted by `profile.service#updateMyProfile`'s own
  // schema all along but silently stripped here (a `z.object` with no
  // matching key drops it, no error), a client could set a height and
  // the write would 200 with nothing actually saved. Fixed alongside the
  // read-side gap in `serializers/profile.ts` (docs/ux-api-review.md §3b).
  heightCm: z.number().int().min(100).max(250).optional(),
  weightG: z.number().int().min(20000).max(300000).optional(),
  weightVisible: z.boolean().optional(),
  bodyType: z.enum(BODY_TYPES).optional(),
  unitPreference: unitPreferenceSchema.optional(),
  distancePrecisionFloorKm: z.number().int().min(1).max(500).nullable().optional(),
  confirmCriticalChange: z.boolean().optional(),
});
const UploadPhotoBodySchema = z.object({ imageUrl: z.string() });
const ReorderPhotosBodySchema = z.object({ orderedPhotoIds: z.array(z.string()) });
// Wiring fix (item 5): the underlying service
// (`behavioralPrompt.service#respondToSuggestion`) now requires an
// importance level or a ladder position for a non-skipped response,
// exactly the same vocabulary `PUT /me/answers`
// (`question.service#PutQuestionAnswerInput`) already uses, but this
// schema previously only accepted `selfValue`/`partnerValue`, so
// answering (not skipping) a prompt could never succeed at all. Also
// widened `selfValue`/`partnerValue` off the old flat 1-5-only shape:
// a behavioral-prompt suggestion can link to ANY question in the typed
// bank (single_choice/multi_choice/frequency, not just scale), the
// service itself is the source of truth for what's a valid value for
// the specific question a suggestion points at (same "route only
// handles params/query, the service validates the body" split
// `src/http/validation.ts`'s file doc already documents for
// `PUT /me/answers`), this route no longer second-guesses that with a
// narrower shape of its own.
const RespondSuggestionBodySchema = z.object({
  skipped: z.boolean().optional(),
  selfValue: z.unknown().optional(),
  partnerValue: z.unknown().optional(),
  importance: z.enum(IMPORTANCE_LEVELS).optional(),
  ladderPosition: z.union([z.literal(0), z.literal(1), z.literal(2), z.literal(3), z.literal(4)]).optional(),
});

export function registerProfileRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/me', auth, async (req, reply) => {
    const { userId } = requireUserActor(req.ctx!);
    const { rows } = await req.ctx!.db.query<UserRow>(
      `SELECT id, email, password_hash, birthdate::text, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at, created_at, last_active_at
       FROM users WHERE id = $1`,
      [userId],
    );
    if (!rows[0]) throw new NotFoundError('Account not found.');
    reply.send(serializeMe(mapUserRow(rows[0])));
  });

  app.patch('/me', auth, async (req, reply) => {
    const { userId } = requireUserActor(req.ctx!);
    const body = parseOrThrow(PatchMeSchema, req.body);

    if (body.email) {
      const email = body.email.toLowerCase();
      const { rows: existing } = await req.ctx!.db.query<{ id: string }>(
        `SELECT id FROM users WHERE email = $1 AND id <> $2`,
        [email, userId],
      );
      if (existing.length > 0) throw new ConflictError('An account with this email already exists.');
      await req.ctx!.db.query(`UPDATE users SET email = $2 WHERE id = $1`, [userId, email]);
    }

    const { rows } = await req.ctx!.db.query<UserRow>(
      `SELECT id, email, password_hash, birthdate::text, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at, created_at, last_active_at
       FROM users WHERE id = $1`,
      [userId],
    );
    reply.send(serializeMe(mapUserRow(rows[0]!)));
  });

  // §29 additions.
  app.delete('/me', auth, async (req, reply) => {
    await profileService.deleteMyAccount(req.ctx!);
    reply.status(204).send();
  });

  app.get('/me/data-export', auth, async (req, reply) => {
    reply.send(await profileService.exportMyData(req.ctx!));
  });

  app.get('/me/profile', auth, async (req, reply) => {
    reply.send(serializeMyProfile(await profileService.getMyProfile(req.ctx!)));
  });

  app.patch('/me/profile', auth, async (req, reply) => {
    const body = parseOrThrow(UpdateProfileBodySchema, req.body);
    reply.send(serializeMyProfile(await profileService.updateMyProfile(req.ctx!, body)));
  });

  // ---- Photos (§7.2) ----
  // `photo.service#listMyPhotos` was fully built and tested but had no
  // route, the own-profile photo grid had no way to reload on app
  // relaunch (docs/ux-api-review.md §3a).
  app.get('/me/photos', auth, async (req, reply) => {
    reply.send(await photoService.listMyPhotos(req.ctx!));
  });

  // Mobile readiness (wiring item 6): an upload retried after a dropped
  // response would otherwise create a second photo row for the same
  // image, see middleware/idempotency.ts.
  app.post('/me/photos', auth, async (req, reply) => {
    const body = parseOrThrow(UploadPhotoBodySchema, req.body);
    const result = await withIdempotencyKey(
      req.ctx!,
      { scope: 'POST /me/photos', key: idempotencyKeyHeader(req), requestBody: body },
      async () => ({ status: 201, body: await photoService.uploadPhoto(req.ctx!, body) }),
    );
    reply.status(result.status).send(result.body);
  });

  app.delete('/me/photos/:photoId', auth, async (req, reply) => {
    const photoId = requireUuidParam(req.params, 'photoId');
    await photoService.deletePhoto(req.ctx!, photoId);
    reply.status(204).send();
  });

  app.post('/me/photos/:photoId/primary', auth, async (req, reply) => {
    const photoId = requireUuidParam(req.params, 'photoId');
    reply.send(await photoService.setPrimaryPhoto(req.ctx!, photoId));
  });

  app.post('/me/photos/reorder', auth, async (req, reply) => {
    const body = parseOrThrow(ReorderPhotosBodySchema, req.body);
    reply.send(await photoService.reorderPhotos(req.ctx!, body.orderedPhotoIds));
  });

  // Wiring fix (item 3, accessibility rule 1): `photoAltText.service.ts`
  // (setPhotoAltText/clearPhotoAltText) was fully built and tested but had
  // no route, so a client had no way to ever SET a photo's description in
  // the first place, even once the read side carries it everywhere (see
  // `photo.service#listMyPhotos`'s `altText` field and the profile/
  // discovery/matches serializers). Never touches photoAltText.service.ts
  // itself, only calls its already-tested exports.
  app.put('/me/photos/:photoId/alt-text', auth, async (req, reply) => {
    const photoId = requireUuidParam(req.params, 'photoId');
    reply.send(await photoAltTextService.setPhotoAltText(req.ctx!, photoId, req.body));
  });

  app.delete('/me/photos/:photoId/alt-text', auth, async (req, reply) => {
    const photoId = requireUuidParam(req.params, 'photoId');
    await photoAltTextService.clearPhotoAltText(req.ctx!, photoId);
    reply.status(204).send();
  });

  // ---- Photo A/B testing (§7.3) ----
  app.get('/me/photo-test-results', auth, async (req, reply) => {
    reply.send(await photoExperimentService.getMyPhotoTestResults(req.ctx!));
  });

  app.post('/me/photo-test-results/:photoId/approve', auth, async (req, reply) => {
    const photoId = requireUuidParam(req.params, 'photoId');
    await photoExperimentService.approveRecommendation(req.ctx!, photoId);
    reply.status(204).send();
  });

  app.post('/me/photo-test-results/:photoId/reject', auth, async (req, reply) => {
    const photoId = requireUuidParam(req.params, 'photoId');
    await photoExperimentService.rejectRecommendation(req.ctx!, photoId);
    reply.status(204).send();
  });

  // ---- Behavioral prompts (§17) ----
  app.get('/me/behavioral-prompts', auth, async (req, reply) => {
    reply.send(await behavioralPromptService.listPendingSuggestions(req.ctx!));
  });

  app.post('/me/behavioral-prompts/:suggestionId/respond', auth, async (req, reply) => {
    const suggestionId = requireUuidParam(req.params, 'suggestionId');
    const body = parseOrThrow(RespondSuggestionBodySchema, req.body);
    // Shape validation only, same "route only handles params/query, the
    // service validates the body" split every other mutation in this
    // codebase uses (see src/http/validation.ts's file doc). In
    // particular this route never fabricates a default `importance` when
    // one wasn't supplied, `respondToSuggestion` itself throws a clear
    // ValidationError naming exactly what's missing rather than this
    // layer inventing a stated preference on the caller's behalf.
    await behavioralPromptService.respondToSuggestion(req.ctx!, suggestionId, {
      skipped: body.skipped ?? false,
      selfValue: body.selfValue,
      partnerValue: body.partnerValue,
      importance: body.importance,
      ladderPosition: body.ladderPosition,
    });
    reply.status(204).send();
  });
}
