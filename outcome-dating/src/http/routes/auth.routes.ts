/**
 * §24.1 Auth routes. All public (no bearer token) — this is the one route
 * group the conformance plan (C-24.1) requires be reachable with no prior
 * access token.
 */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as authService from '../../services/auth.service.js';
import { ValidationError } from '../../lib/errors.js';
import { serializeMe } from '../serializers/user.js';
import type { AppDeps } from '../deps.js';
import { systemCtx } from '../deps.js';
import { authenticate } from '../auth.js';
import type { InMemoryRateLimiter } from '../rateLimit.js';
import { parseOrThrow } from '../validation.js';

const RegisterBodySchema = z.object({
  email: z.string(),
  password: z.string(),
  birthdate: z.string(),
  /** §5.1 rule 4 — spec-facing field name; translated to `RegisterInput.acceptedTermsAt` below. */
  termsAccepted: z.boolean(),
  city: z.string().optional(),
  locationPermission: z.boolean().optional(),
});

const LoginBodySchema = z.object({
  email: z.string(),
  password: z.string(),
  deviceFingerprint: z.string().optional(),
});

const RefreshBodySchema = z.object({ refreshToken: z.string() });
const ForgotPasswordBodySchema = z.object({ email: z.string() });
const ResetPasswordBodySchema = z.object({ resetToken: z.string(), newPassword: z.string() });
const VerifyEmailBodySchema = z.object({ token: z.string() });

// Optional phone number (build correction — see auth.service.ts module doc).
const RequestPhoneBodySchema = z.object({ phoneNumber: z.string(), country: z.string() });
const VerifyPhoneBodySchema = z.object({ code: z.string() });

export function registerAuthRoutes(app: FastifyInstance, deps: AppDeps, limiter: InMemoryRateLimiter): void {
  // §19.2 device/network-abuse rate limiting on the three endpoints most
  // valuable to a bot: credential stuffing, account-creation spam, and
  // password-reset-triggered email flooding / email-enumeration probing.
  const authAbuseGuard = (routeKey: string, max: number) => (req: { ip: string }) => {
    limiter.check(`${routeKey}:${req.ip}`, { max, windowMs: 60_000 });
  };

  app.post('/auth/register', async (req, reply) => {
    authAbuseGuard('register', 10)(req);
    const body = parseOrThrow(RegisterBodySchema, req.body);
    if (body.termsAccepted !== true) {
      throw new ValidationError('You must accept the terms to register.', { field: 'termsAccepted' });
    }
    const ctx = systemCtx(deps, 'http.auth.register');
    const { user, tokens } = await authService.register(ctx, {
      email: body.email,
      password: body.password,
      birthdate: body.birthdate,
      acceptedTermsAt: ctx.clock.now(),
      city: body.city,
      locationPermissionGranted: body.locationPermission,
    });
    reply.status(201).send({ user: serializeMe(user), tokens });
  });

  app.post('/auth/login', async (req, reply) => {
    authAbuseGuard('login', 20)(req);
    const body = parseOrThrow(LoginBodySchema, req.body);
    const ctx = systemCtx(deps, 'http.auth.login');
    const { user, tokens } = await authService.login(ctx, {
      email: body.email,
      password: body.password,
      deviceFingerprint: body.deviceFingerprint,
      ipAddress: req.ip,
    });
    reply.send({ user: serializeMe(user), tokens });
  });

  app.post('/auth/logout', async (req, reply) => {
    const body = parseOrThrow(RefreshBodySchema, req.body);
    await authService.logout(systemCtx(deps, 'http.auth.logout'), { refreshToken: body.refreshToken });
    reply.status(204).send();
  });

  app.post('/auth/refresh', async (req, reply) => {
    const body = parseOrThrow(RefreshBodySchema, req.body);
    const tokens = await authService.refresh(systemCtx(deps, 'http.auth.refresh'), { refreshToken: body.refreshToken });
    reply.send({ tokens });
  });

  app.post('/auth/forgot-password', async (req, reply) => {
    authAbuseGuard('forgot-password', 5)(req);
    const body = parseOrThrow(ForgotPasswordBodySchema, req.body);
    await authService.forgotPassword(systemCtx(deps, 'http.auth.forgot_password'), { email: body.email });
    // Always 202, regardless of whether the email exists — auth.service
    // itself never leaks that; the route must not either.
    reply.status(202).send({ status: 'ok' });
  });

  app.post('/auth/reset-password', async (req, reply) => {
    const body = parseOrThrow(ResetPasswordBodySchema, req.body);
    await authService.resetPassword(systemCtx(deps, 'http.auth.reset_password'), {
      resetToken: body.resetToken,
      newPassword: body.newPassword,
    });
    reply.status(204).send();
  });

  // Additions beyond the frozen §24.1 list (flagged in auth.service.ts's
  // own module doc as needing HTTP wiring): email verification issue/consume.
  app.post('/auth/resend-verification', { preHandler: authenticate(deps) }, async (req, reply) => {
    await authService.requestEmailVerification(req.ctx!);
    reply.status(202).send({ status: 'ok' });
  });

  app.post('/auth/verify-email', async (req, reply) => {
    const body = parseOrThrow(VerifyEmailBodySchema, req.body);
    await authService.verifyEmail(systemCtx(deps, 'http.auth.verify_email'), { token: body.token });
    reply.status(204).send();
  });

  // ---- Optional phone number (build correction — never mandatory; see
  // auth.service.ts module doc). All four require an authenticated user —
  // a phone is something a logged-in account manages, never a registration
  // input. Responses are built inline here rather than through
  // `src/http/serializers/*` — `getMyPhoneStatus` already returns a masked,
  // owner-only view (never the full E.164 number, see its own doc), so
  // there is nothing left for a serializer layer to strip. ----
  app.post('/auth/phone', { preHandler: authenticate(deps) }, async (req, reply) => {
    const body = parseOrThrow(RequestPhoneBodySchema, req.body);
    await authService.requestPhoneVerification(req.ctx!, { phoneNumber: body.phoneNumber, country: body.country });
    reply.status(202).send({ status: 'ok' });
  });

  app.post('/auth/phone/verify', { preHandler: authenticate(deps) }, async (req, reply) => {
    const body = parseOrThrow(VerifyPhoneBodySchema, req.body);
    await authService.verifyPhone(req.ctx!, { code: body.code });
    reply.status(204).send();
  });

  app.delete('/auth/phone', { preHandler: authenticate(deps) }, async (req, reply) => {
    await authService.removePhone(req.ctx!);
    reply.status(204).send();
  });

  app.get('/auth/phone', { preHandler: authenticate(deps) }, async (req, reply) => {
    const status = await authService.getMyPhoneStatus(req.ctx!);
    reply.send({
      hasPhone: status.hasPhone,
      verified: status.verified,
      countryCode: status.countryCode,
      last2: status.last2,
      addedAt: status.addedAt ? status.addedAt.toISOString() : null,
      verifiedAt: status.verifiedAt ? status.verifiedAt.toISOString() : null,
    });
  });
}
