/** §24.8 Dates routes (venues + date proposals). */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as venueService from '../../services/venue.service.js';
import * as dateProposalService from '../../services/dateProposal.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { coerceDate, parseOrThrow, requireUuidParam } from '../validation.js';

const VenueCategorySchema = z
  .enum(['coffee', 'dessert', 'drinks', 'walk', 'museum', 'arcade', 'live_music', 'comedy', 'class_activity', 'food_market'])
  .optional();

const ProposeDateBodySchema = z.object({
  venueId: z.string(),
  scheduledStart: z.string().or(z.date()),
  scheduledEnd: z.string().or(z.date()),
  optionalNote: z.string().optional(),
});

const FeedbackBodySchema = z.object({
  positive: z.boolean(),
  wouldMeetAgain: z.boolean().optional(),
  safetyConcern: z.boolean().optional(),
  notes: z.string().optional(),
});

export function registerDateRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/venues', auth, async (req, reply) => {
    const category = VenueCategorySchema.parse((req.query as { category?: string } | undefined)?.category);
    reply.send(await venueService.listActiveVenues(req.ctx!, category ? { category } : undefined));
  });

  app.get('/venues/:venueId/time-slots', auth, async (req, reply) => {
    const venueId = requireUuidParam(req.params, 'venueId');
    const q = req.query as { from?: string; to?: string };
    const from = q.from ? coerceDate(q.from, 'from') : req.ctx!.clock.now();
    const to = q.to ? coerceDate(q.to, 'to') : new Date(from.getTime() + 30 * 24 * 60 * 60 * 1000);
    reply.send(await venueService.listAvailableTimeSlots(req.ctx!, venueId, from, to));
  });

  app.post('/conversations/:conversationId/date-proposals', auth, async (req, reply) => {
    const conversationId = requireUuidParam(req.params, 'conversationId');
    const body = parseOrThrow(ProposeDateBodySchema, req.body);
    reply.status(201).send(
      await dateProposalService.proposeDate(req.ctx!, {
        conversationId,
        venueId: body.venueId,
        scheduledStart: coerceDate(body.scheduledStart, 'scheduledStart'),
        scheduledEnd: coerceDate(body.scheduledEnd, 'scheduledEnd'),
        optionalNote: body.optionalNote,
      }),
    );
  });

  app.get('/date-proposals/:dateProposalId', auth, async (req, reply) => {
    const dateProposalId = requireUuidParam(req.params, 'dateProposalId');
    reply.send(await dateProposalService.getDateProposal(req.ctx!, dateProposalId));
  });

  app.post('/date-proposals/:dateProposalId/accept', auth, async (req, reply) => {
    const dateProposalId = requireUuidParam(req.params, 'dateProposalId');
    reply.send(await dateProposalService.acceptDateProposal(req.ctx!, dateProposalId));
  });

  app.post('/date-proposals/:dateProposalId/decline', auth, async (req, reply) => {
    const dateProposalId = requireUuidParam(req.params, 'dateProposalId');
    reply.send(await dateProposalService.declineDateProposal(req.ctx!, dateProposalId));
  });

  app.post('/date-proposals/:dateProposalId/cancel', auth, async (req, reply) => {
    const dateProposalId = requireUuidParam(req.params, 'dateProposalId');
    reply.send(await dateProposalService.cancelDateProposal(req.ctx!, dateProposalId));
  });

  app.post('/date-proposals/:dateProposalId/confirm-attendance', auth, async (req, reply) => {
    const dateProposalId = requireUuidParam(req.params, 'dateProposalId');
    reply.send(await dateProposalService.confirmAttendance(req.ctx!, dateProposalId));
  });

  app.post('/date-proposals/:dateProposalId/feedback', auth, async (req, reply) => {
    const dateProposalId = requireUuidParam(req.params, 'dateProposalId');
    const body = parseOrThrow(FeedbackBodySchema, req.body);
    reply.status(201).send(await dateProposalService.submitPostDateFeedback(req.ctx!, dateProposalId, body));
  });
}
