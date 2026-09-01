# Outcome-Aligned Dating App: Backend

A TypeScript/Fastify/Postgres backend for a dating app built around one idea: the product it sells is a completed real-world date, not attention inside the app. Matching is filter-then-sort, never swipe-then-addict, and a mutual match starts a structured date proposal that puts real money in escrow on both sides, so a date happening (or not) has a consequence. There is no generative AI anywhere in the user-facing product; notification copy and safety banners are static templates, and message scanning is regex/keyword-based, not a model.

The full product rationale is in [`SPEC.md`](./SPEC.md). This backend implements that spec; [`docs/architecture.md`](./docs/architecture.md) is the companion for someone about to change code (module graph, invariants, extension points).

## Quickstart

Every command below was run against this repository to confirm it works (Node 22, Postgres 16 server binaries at `/usr/lib/postgresql/16/bin`, root shell). If your environment lacks a system Postgres 16 install there, adapt `scripts/pg-dev.sh` or point `DATABASE_URL` at your own instance instead of using `pg:start`.

```bash
npm install

# Start a local Postgres 16 cluster (idempotent, must run as root). Creates
# the outcome_dating role/database on first run, listening on 127.0.0.1:55433.
npm run pg:start

# Copy the example env (defaults already match pg:start's port/db name).
cp .env.example .env

# Apply every migration in db/migrations/, in filename order.
npm run migrate

# Seed deterministic dev data: config defaults, feature flags, the typed
# question bank, interest tags, venues, and 20 users (@seed.outcome-dating.test).
npm run seed

# Run the API and background job scheduler.
npm run dev
```

`GET http://localhost:3000/healthz` returns `{"status":"ok"}` once it's up. `GET /admin/system-readiness` (admin-only) reports which adapter is live for each external integration.

Run the test suite (type-checks first, then runs every test file against a real, locally-migrated Postgres):

```bash
npm test
```

Other useful commands, all verified: `npm run pg:stop` / `npm run pg:reset` (stop the cluster / wipe `.pgdata` and start fresh); `npm run build && npm start` (compile to `dist/` and run it); `node --import tsx src/index.ts jobs:run <name>` (run one background job once); `node --import tsx src/index.ts jobs:start` (run only the scheduler, no HTTP server).

## Where things live

| Path | What's there |
|---|---|
| `src/http/routes/*.routes.ts` | Fastify handlers: parse/validate input, call one service function, serialize the result. No business logic here. |
| `src/http/serializers/*.ts` | Explicit allowlist serializers, the only place a DB row becomes a wire response. |
| `src/services/*.service.ts` | Business logic, one file per bounded concern. Every exported function's first parameter is `Ctx` (`src/lib/ctx.ts`). |
| `src/services/payments/`, `src/services/media/`, `src/services/notifications/` | Ports and adapters for the five external integrations (payments, photo moderation, push, email, SMS). Each has a fake used everywhere outside production; only payments has a real (stub) adapter written. |
| `src/domain/` | Pure, side-effect-free logic and shared types: entity shapes, the question-bank scoring engine, unit conversion, the i18n catalogue. Never touches `Ctx` or the database. |
| `src/jobs/*.job.ts` | Background jobs, thin named wrappers around service functions, registered in `src/jobs/registry.ts`. |
| `src/config/` | `env.ts` (deployment settings, read once at startup) and `config.service.ts` (business variables, admin-tunable at runtime with no redeploy). `adapters.ts` selects every external adapter as a function of `NODE_ENV` and refuses to boot in production with a fake one wired in. |
| `db/migrations/*.sql` | The schema, applied in filename order by `npm run migrate`. No ORM. |
| `tests/unit/`, `tests/http/`, `tests/jobs/`, `tests/concurrency/`, `tests/perf/` | Pure/DB-backed unit tests, routes through a real Fastify instance, jobs run directly against a controllable clock, true concurrent-race tests, and two seeded-at-scale performance suites. |
| `SPEC.md` | The original product specification: the ground truth for why a rule exists. |
| `INTERFACES.md` | The frozen module-boundary contract from the first build pass. |
| `docs/` | Architecture, testing, and review documents. Start at [`docs/README.md`](./docs/README.md) for an index of what to read and when. |

## Known limitations

- **No real payment processor.** `StripeProcessor` throws `NotImplementedError` on every method; the `stripe` package isn't a dependency. The production startup guard refuses to boot with anything else configured, so this can't ship silently, but real payments require writing this adapter from its documented contract.
- **No real photo/content moderation.** The stub adapter approves virtually any photo by URL heuristic. No real `ImageModerationPort` implementation exists yet, and the production guard refuses to boot without one.
- **No real push, email, or SMS provider.** All three are documented stubs; the delivery pipeline (outbox, retry/backoff, quiet hours, preferences) is fully built and tested against fakes.
- **The scaling ceiling is real, and partially addressed.** Discovery and compatibility scoring are now geographically bounded (see `docs/architecture.md`), but a single Postgres primary, an in-process rate limiter, and an in-process job scheduler all remain hard limits the moment the app tier is scaled to more than one instance. See [`docs/capacity.md`](./docs/capacity.md) for the numbers.
- **Legal and safety review findings.** An adversarial review found real gaps (money-transmission licensing, age assurance, moderation appeal fairness); several have since been fixed in code and some have not been re-verified. See [`docs/risk-review.md`](./docs/risk-review.md) before a real-money launch.
