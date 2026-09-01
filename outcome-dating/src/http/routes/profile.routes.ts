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
import * as photoExperimentService from '../../services/photoExperiment.service.js';
import * as behavioralPromptService from '../../services/behavioralPrompt.service.js';
import { ConflictError, NotFoundError, ValidationError } from '../../lib/errors.js';
import { requireUserActor } from '../../lib/ctx.js';
import type { User } from '../../domain/types.js';
import { serializeMe } from '../serializers/user.js';
import { serializeMyProfile } from '../serializers/profile.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow, requireUuidParam } from '../validation.js';

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
  confirmCriticalChange: z.boolean().optional(),
});
const UploadPhotoBodySchema = z.object({ imageUrl: z.string() });
const ReorderPhotosBodySchema = z.object({ orderedPhotoIds: z.array(z.string()) });
const RespondSuggestionBodySchema = z.object({
  skipped: z.boolean().optional(),
  selfValue: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5), z.null()]).optional(),
  partnerValue: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5), z.null()]).optional(),
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
  // route — the own-profile photo grid had no way to reload on app
  // relaunch (docs/ux-api-review.md §3a).
  app.get('/me/photos', auth, async (req, reply) => {
    reply.send(await photoService.listMyPhotos(req.ctx!));
  });

  app.post('/me/photos', auth, async (req, reply) => {
    const body = parseOrThrow(UploadPhotoBodySchema, req.body);
    reply.status(201).send(await photoService.uploadPhoto(req.ctx!, body));
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
    if (!body.skipped && (body.selfValue === undefined || body.partnerValue === undefined)) {
      throw new ValidationError('Both selfValue and partnerValue are required when not skipping.');
    }
    await behavioralPromptService.respondToSuggestion(req.ctx!, suggestionId, {
      skipped: body.skipped ?? false,
      selfValue: body.selfValue,
      partnerValue: body.partnerValue,
    });
    reply.status(204).send();
  });
}
