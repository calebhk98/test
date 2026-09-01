/**
 * src/http/routes/health.routes.ts, operator-facing startup readiness.
 *
 * `GET /healthz` (registered directly in `src/http/server.ts`, not here)
 * is the public, unauthenticated liveness probe, it must stay a trivial
 * "is the process up" check for load balancers and must never leak
 * configuration.
 *
 * `GET /admin/system-readiness` here is the different thing the
 * production-guard build brief asks for: "a single structured summary
 * ... expose it on an operator-facing endpoint that does not leak secrets
 * and is not reachable by ordinary users." It reuses
 * `buildReadinessReport`, the exact same per-capability report logged at
 * startup (`src/index.ts`), so an operator can confirm live, without a
 * redeploy or a log search, whether the running process is on fakes.
 * `admin`-only (`requireRole('admin')`, same pattern as every other
 * `src/http/routes/admin.routes.ts` route), never reachable by a plain
 * user or venue-staff token. Every field in `ReadinessEntry` is a
 * provider name, a boolean, or a secret-free status string
 * (`src/config/adapters.ts`'s own doc/tests guarantee this), nothing
 * here can leak an actual secret value.
 */
import type { FastifyInstance } from 'fastify';
import { buildReadinessReport } from '../../config/adapters.js';
import { getEnv } from '../../config/env.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';

export function registerHealthRoutes(app: FastifyInstance, deps: AppDeps): void {
  app.get('/admin/system-readiness', { preHandler: [authenticate(deps), requireRole('admin')] }, async (_req, reply) => {
    reply.send(buildReadinessReport(getEnv()));
  });
}
