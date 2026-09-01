/**
 * src/http/server.ts — builds (but does not start) the Fastify application.
 *
 * `buildServer(deps)` is the single entry point both `src/index.ts`'s
 * `serve` command and every `tests/http/*.test.ts` file use — tests call
 * `app.inject(...)` directly against the returned instance (no real
 * network socket, no port binding), per the task brief.
 *
 * See `src/http/routeTable.ts` for the full route -> spec-section coverage
 * table this file's registrations are audited against.
 */
import Fastify from 'fastify';
import type { FastifyInstance } from 'fastify';
import { fastifyErrorHandler } from './errors.js';
import { InMemoryRateLimiter } from './rateLimit.js';
import type { AppDeps } from './deps.js';
import { registerAuthRoutes } from './routes/auth.routes.js';
import { registerProfileRoutes } from './routes/profile.routes.js';
import { registerQuestionsRoutes } from './routes/questions.routes.js';
import { registerFilterRoutes } from './routes/filters.routes.js';
import { registerDiscoveryRoutes } from './routes/discovery.routes.js';
import { registerInterestRoutes } from './routes/interests.routes.js';
import { registerConversationRoutes } from './routes/conversations.routes.js';
import { registerMatchRoutes } from './routes/matches.routes.js';
import { registerDateRoutes } from './routes/dates.routes.js';
import { registerTicketRoutes } from './routes/tickets.routes.js';
import { registerPaymentRoutes } from './routes/payments.routes.js';
import { registerTrustRoutes } from './routes/trust.routes.js';
import { registerReportRoutes } from './routes/reports.routes.js';
import { registerAdminRoutes } from './routes/admin.routes.js';

declare module 'fastify' {
  interface FastifyInstance {
    rateLimiter: InMemoryRateLimiter;
  }
}

export function buildServer(deps: AppDeps): FastifyInstance {
  const app = Fastify({ logger: false });
  const limiter = new InMemoryRateLimiter(deps.clock);

  app.decorateRequest('ctx', undefined);
  // Exposed mainly for `tests/http/*.test.ts`, which register many
  // accounts per file against one shared limiter instance and need to
  // reset counters between scenarios — production code never calls this.
  app.decorate('rateLimiter', limiter);
  app.setErrorHandler(fastifyErrorHandler);

  app.get('/healthz', async () => ({ status: 'ok' }));

  registerAuthRoutes(app, deps, limiter);
  registerProfileRoutes(app, deps);
  registerQuestionsRoutes(app, deps);
  registerFilterRoutes(app, deps);
  registerDiscoveryRoutes(app, deps);
  registerInterestRoutes(app, deps);
  registerConversationRoutes(app, deps);
  registerMatchRoutes(app, deps);
  registerDateRoutes(app, deps);
  registerTicketRoutes(app, deps);
  registerPaymentRoutes(app, deps);
  registerTrustRoutes(app, deps);
  registerReportRoutes(app, deps);
  registerAdminRoutes(app, deps);

  return app;
}
