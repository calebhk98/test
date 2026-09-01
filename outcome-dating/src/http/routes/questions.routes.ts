/** §24.3 Questions routes. */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as questionService from '../../services/question.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow } from '../validation.js';

const AnswerSchema = z.object({
  questionId: z.string(),
  selfValue: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5), z.null()]),
  partnerValue: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5), z.null()]),
});
const PutAnswersBodySchema = z.array(AnswerSchema);

export function registerQuestionsRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/questions', auth, async (req, reply) => {
    reply.send(await questionService.listActiveQuestions(req.ctx!));
  });

  app.get('/me/answers', auth, async (req, reply) => {
    reply.send(await questionService.getMyAnswers(req.ctx!));
  });

  app.put('/me/answers', auth, async (req, reply) => {
    const body = parseOrThrow(PutAnswersBodySchema, req.body);
    reply.send(await questionService.putMyAnswers(req.ctx!, body));
  });
}
