/** §24.4 Filters routes. */
import type { FastifyInstance } from 'fastify';
import { z } from 'zod';
import * as filterService from '../../services/filter.service.js';
import type { AppDeps } from '../deps.js';
import { authenticate, requireRole } from '../auth.js';
import { parseOrThrow } from '../validation.js';

const FilterOperatorSchema = z.enum(['eq', 'neq', 'gte', 'lte', 'gt', 'lt', 'in']);
const UpdateFiltersBodySchema = z.array(
  z.object({
    filterKey: z.string(),
    operator: FilterOperatorSchema,
    value: z.unknown(),
    enabled: z.boolean(),
  }),
);

export function registerFilterRoutes(app: FastifyInstance, deps: AppDeps): void {
  const auth = { preHandler: [authenticate(deps), requireRole('user')] };

  app.get('/me/filters', auth, async (req, reply) => {
    reply.send(await filterService.getMyFilters(req.ctx!));
  });

  app.patch('/me/filters', auth, async (req, reply) => {
    const body = parseOrThrow(UpdateFiltersBodySchema, req.body);
    // Zod's `.unknown()` field type-infers as optional (`value?: unknown`)
    // even though every element in the array is always given a `value` key
    // by the client (possibly `null`/`undefined` as a legitimate value, not
    // a missing key) — rebuild each element explicitly so the resulting
    // array structurally satisfies `UpdateFilterInput`'s required `value`.
    const input = body.map((f) => ({ filterKey: f.filterKey, operator: f.operator, value: f.value, enabled: f.enabled }));
    reply.send(await filterService.updateMyFilters(req.ctx!, input));
  });
}
