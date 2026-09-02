/**
 * §24.7 Conversations routes.
 *
 * ROLE BOUNDARY (spec §4.2, C-4.2.4): every route here is `requireRole('user')`
 * only, a venue-staff or admin token gets a 403 `forbidden` before any
 * handler runs, enforced by `src/http/auth.ts`. This is the primary "venue
 * staff cannot see chats" gate; `redemption.service.ts`'s own structural
 * narrowness (never touching `messages`) is the second, independent layer.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as conversationService from '../../services/conversation.service.js';
import * as messageService from '../../services/message.service.js';
import * as timelineService from '../../services/timeline.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { paginationQuerySchema, parseOrThrow, requireUuidParam } from '../validation.js';
import { serializeTimelinePage } from '../serializers/timeline.js';
import { withIdempotencyKey, idempotencyKeyHeader } from '../middleware/idempotency.js';

const SendMessageBodySchema = z.object({ body: z.string() });
const MarkReadBodySchema = z.object({ uptoMessageId: z.string() });
const StatusQuerySchema = z.object({ status: z.enum(['active', 'cooling', 'archived', 'established']).optional() });

export function registerConversationRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/conversations', auth, async (req, reply) => {
    const query = parseOrThrow(StatusQuerySchema, req.query);
    reply.send(await conversationService.listMyConversations(req.ctx!, query));
  });

  app.get('/conversations/:conversationId', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    reply.send(await conversationService.getConversation(req.ctx!, conversationId));
  });

  app.get('/conversations/:conversationId/messages', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(await messageService.listMessages(req.ctx!, conversationId, query));
  });

  // Mobile readiness (wiring item 6): unlike `sendInterest`, `sendMessage`
  // has no unique-pair constraint to fall back on, a retried post with no
  // `Idempotency-Key` genuinely double-sends the same message today. A
  // caller that supplies one is protected; see middleware/idempotency.ts.
  app.post('/conversations/:conversationId/messages', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    const body = parseOrThrow(SendMessageBodySchema, req.body);
    const result = await withIdempotencyKey(
      req.ctx!,
      { scope: 'POST /conversations/:conversationId/messages', key: idempotencyKeyHeader(req), requestBody: { conversationId, ...body } },
      async () => ({ status: 201, body: await messageService.sendMessage(req.ctx!, conversationId, body.body) }),
    );
    reply.status(result.status).send(result.body);
  });

  app.post('/conversations/:conversationId/archive', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    reply.send(await conversationService.archiveConversation(req.ctx!, conversationId));
  });

  app.post('/conversations/:conversationId/read', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    const body = parseOrThrow(MarkReadBodySchema, req.body);
    await messageService.markRead(req.ctx!, conversationId, body.uptoMessageId);
    reply.status(204).send();
  });

  // Product-owner finding #2/#3, see timeline.service.ts. Addition, not a
  // literal §24.7 route: merged messages + date-proposal lifecycle events
  // for one conversation, cursor-paginated.
  app.get('/conversations/:conversationId/timeline', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    const query = parseOrThrow(paginationQuerySchema, req.query);
    reply.send(serializeTimelinePage(await timelineService.getConversationTimeline(req.ctx!, conversationId, query)));
  });
}
