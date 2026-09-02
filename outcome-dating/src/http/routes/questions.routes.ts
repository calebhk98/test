/**
 * §24.3 Questions routes, the ONE typed question bank
 * (db/migrations/008_questions.sql). Replaces the old flat 1-5
 * self/partner-pair bank's routes entirely; see
 * src/services/question.service.ts's file-level CUTOVER doc for exactly
 * what moved and the (fully documented) residual exception.
 *
 * `GET /questions`, `GET /me/answers`, `PUT /me/answers` are the three
 * paths `tests/http/routeTable.test.ts` hardcodes as required §24.3
 * routes, kept at those exact paths/methods, repointed to the new bank
 * underneath. Every other route here is an addition (see routeTable.ts).
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as questionService from '../../services/question.service.js';
import type { TagIntensity } from '../../domain/questions/index.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow, requireUuidParam } from '../validation.js';
import { serializeMyAnswer, serializeQuestionBankPage, serializeQuestionCard } from '../serializers/questions.js';
import { resolveRequestLocale } from '../middleware/locale.js';

const ListQuestionsQuerySchema = z.object({
  category: z.string().min(1).max(100).optional(),
  cursor: z.string().optional(),
  limit: z.coerce.number().int().min(1).max(200).optional(),
});

const NextQuestionsQuerySchema = z.object({
  count: z.coerce.number().int().min(1).max(50).optional(),
});

const SetTagIntensityBodySchema = z.object({
  intensity: z.string(),
});

const SetAvoidTagsBodySchema = z.object({
  tagIds: z.array(z.string()),
});

export function registerQuestionsRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  // ---- The bank itself ----

  app.get('/questions', auth, async (req, reply) => {
    const query = parseOrThrow(ListQuestionsQuerySchema, req.query);
    // Localization wiring: honour the caller's negotiated locale (stored
    // preference over Accept-Language header, see middleware/locale.ts),
    // falling back to the question's own English text when no translation
    // exists (question.service#localizeDefinitions).
    const locale = await resolveRequestLocale(req.ctx!, req);
    const page = await questionService.listActiveQuestionBank(req.ctx!, { ...query, locale });
    reply.send(serializeQuestionBankPage(page));
  });

  // Addition, "what should we ask this user next" (src/domain/questions/selector.ts).
  app.get('/questions/next', auth, async (req, reply) => {
    const query = parseOrThrow(NextQuestionsQuerySchema, req.query);
    const locale = await resolveRequestLocale(req.ctx!, req);
    const questions = await questionService.selectNextQuestionsForMe(req.ctx!, { count: query.count, locale });
    reply.send({ items: questions.map(serializeQuestionCard) });
  });

  // ---- The caller's own answers ----

  app.get('/me/answers', auth, async (req, reply) => {
    const answers = await questionService.getMyQuestionAnswers(req.ctx!);
    reply.send(answers.map(serializeMyAnswer));
  });

  // Body shape: src/services/question.service.ts#PutQuestionAnswerInput
  // (slug, status, and either ladderPosition or preferenceValue+importance
  // for an "answered" status), validated by `putMyQuestionAnswer` itself
  // (see src/http/validation.ts's file doc: bodies are validated by the
  // service, this route layer only handles params/query).
  app.put('/me/answers', auth, async (req, reply) => {
    const record = await questionService.putMyQuestionAnswer(req.ctx!, req.body as questionService.PutQuestionAnswerInput);
    reply.send(serializeMyAnswer(record));
  });

  // ---- Tag intensity + avoidance (src/domain/questions/tags.ts) ----

  app.get('/me/tag-intensity', auth, async (req, reply) => {
    reply.send(await questionService.getMyTagIntensities(req.ctx!));
  });

  app.put('/me/tag-intensity/:tagId', auth, async (req, reply) => {
    const tagId = requireUuidParam(req.params, 'tagId');
    const body = parseOrThrow(SetTagIntensityBodySchema, req.body);
    const record = await questionService.setMyTagIntensity(req.ctx!, tagId, body.intensity as TagIntensity);
    reply.send(record);
  });

  app.get('/me/avoid-tags', auth, async (req, reply) => {
    reply.send(await questionService.getMyAvoidTagIds(req.ctx!));
  });

  app.put('/me/avoid-tags', auth, async (req, reply) => {
    const body = parseOrThrow(SetAvoidTagsBodySchema, req.body);
    reply.send(await questionService.setMyAvoidTags(req.ctx!, body.tagIds));
  });
}
