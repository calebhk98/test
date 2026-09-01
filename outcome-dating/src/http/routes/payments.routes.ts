/**
 * §24.10 Payments routes: user-facing payment methods, and the processor
 * webhook (§24.10, §25.9).
 *
 * WEBHOOK SIGNATURE VERIFICATION (spec §24.10, C-24.5, "validates the
 * processor's webhook signature before trusting the payload"): the payload
 * must carry an `X-Webhook-Signature` header equal to
 * `hex(hmac-sha256(secret, JSON.stringify(body)))`. `secret` is
 * `STRIPE_WEBHOOK_SECRET` when `PAYMENT_PROCESSOR=stripe` (the real
 * production secret); for the MVP `fake` processor there is no real
 * processor-issued secret to check against, so, mirroring
 * `voucher.service.ts`'s own documented choice to reuse `AUTH_TOKEN_SECRET`
 * rather than invent a new env var outside this agent's ownership of
 * `src/config/env.ts`, the same secret is reused here for the dev/test
 * path. Either way, a request with a missing or incorrect signature is
 * rejected with 401 BEFORE `payment.handleProcessorWebhook` ever sees the
 * body, the handler is never the only path that can move money on an
 * unverified request.
 */
import type { FastifyInstance } from 'fastify';
import { createHmac, timingSafeEqual } from 'node:crypto';
import { z } from 'zod';
import * as paymentService from '../../services/payment.service.js';
import { UnauthorizedError } from '../../lib/errors.js';
import { getEnv } from '../../config/env.js';
import { serializePaymentMethod } from '../serializers/payment.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { systemCtx } from '../deps.js';
import { parseOrThrow, requireUuidParam } from '../validation.js';

const AddPaymentMethodBodySchema = z.object({
  processorToken: z.string(),
  brand: z.string().optional(),
  last4: z.string().optional(),
  makeDefault: z.boolean().optional(),
});

function webhookSecret(): string {
  const env = getEnv();
  return env.PAYMENT_PROCESSOR === 'stripe' && env.STRIPE_WEBHOOK_SECRET ? env.STRIPE_WEBHOOK_SECRET : env.AUTH_TOKEN_SECRET;
}

export function verifyWebhookSignature(rawBody: string, signatureHeader: string | undefined): boolean {
  if (!signatureHeader) return false;
  const expected = createHmac('sha256', webhookSecret()).update(rawBody).digest('hex');
  const expectedBuf = Buffer.from(expected, 'hex');
  const providedBuf = Buffer.from(signatureHeader, 'hex');
  if (expectedBuf.length !== providedBuf.length) return false;
  return timingSafeEqual(expectedBuf, providedBuf);
}

export function signWebhookPayload(body: unknown): string {
  return createHmac('sha256', webhookSecret()).update(JSON.stringify(body)).digest('hex');
}

export function registerPaymentRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.post('/payment-methods', auth, async (req, reply) => {
    const body = parseOrThrow(AddPaymentMethodBodySchema, req.body);
    reply.status(201).send(serializePaymentMethod(await paymentService.addPaymentMethod(req.ctx!, body)));
  });

  app.get('/payment-methods', auth, async (req, reply) => {
    const methods = await paymentService.listPaymentMethods(req.ctx!);
    reply.send(methods.map(serializePaymentMethod));
  });

  app.delete('/payment-methods/:paymentMethodId', auth, async (req, reply) => {
    const paymentMethodId = requireUuidParam(req.params, 'paymentMethodId');
    await paymentService.deletePaymentMethod(req.ctx!, paymentMethodId);
    reply.status(204).send();
  });

  // Public (no bearer token, the processor calls this, not a logged-in
  // user) but signature-gated. §25.9: idempotent, `handleProcessorWebhook`
  // itself no-ops on a replayed event (dup ledger-row check).
  app.post('/webhooks/payments', async (req, reply) => {
    const signature = req.headers['x-webhook-signature'];
    const raw = JSON.stringify(req.body);
    if (Array.isArray(signature) || !verifyWebhookSignature(raw, signature)) {
      throw new UnauthorizedError('Invalid or missing webhook signature.');
    }
    await paymentService.handleProcessorWebhook(systemCtx(deps, 'http.webhook.payments'), req.body);
    reply.status(204).send();
  });
}
