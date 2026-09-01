# Documentation index

One line per document: who should read it, and when. Start with `../README.md` if you haven't.

## Reference (how the system works)

- **[`architecture.md`](./architecture.md)**: read before adding a new service module or cross-service call. The module dependency graph, the invariants that must never break, and the extension points (new question type, notification event, background job, payment adapter).
- **[`test-strategy.md`](./test-strategy.md)**: read before writing a new test. The fake processor's failure-injection contract, the controllable-clock discipline, what's downgraded to a port-contract test.
- **[`conformance.md`](./conformance.md)**: read when writing a new test and wanting to know what "done" looks like, or checking whether a spec rule has a test at all. A 411-row obligation checklist; has its own summary at the top.
- **[`retention.md`](./retention.md)**: read before privacy/legal review, or before adding a new table that will grow unboundedly. The data-retention table: every accumulating data class, its window, delete-vs-anonymize, and why.
- **[`accessibility.md`](./accessibility.md)**: read when building or reviewing a client against this API. What the backend guarantees (alt text, non-color-only status) versus what's entirely the client's job.
- **[`localization.md`](./localization.md)**: read when adding a locale or a user-facing string. The static-catalogue architecture, fallback chain, and Intl-backed formatting.
- **[`capacity.md`](./capacity.md)**: read for capacity planning or a launch-readiness review. Hard numbers at 10K to 8B users, measured where possible.
- **[`normalization.md`](./normalization.md)**: read before touching a table with more than one writer. A table-by-table normal-form audit, with the handful of tables that are one bad UPDATE away from an inconsistent row.
- **[`matrix-scoring.md`](./matrix-scoring.md)**: read only if considering a batched-matrix rewrite of compatibility scoring. The verdict (reject, for the current call shape) and the benchmark numbers behind it.

## Review and analysis (what's been found, what's still open)

Each of these was a snapshot at a point in time; each now leads with what's been fixed since, so a stale finding is never presented as current.

- **[`risk-review.md`](./risk-review.md)**: read before touching moderation, trust, safety, or payments, or before a real-money launch. An adversarial safety/legal/product review, cross-checked against code. Folds in a second, independent spec-only review that reached compatible conclusions.
- **[`duplication.md`](./duplication.md)**: read before touching trust-score exposure, cursor pagination, or distance calculation. An audit of duplicated or divergent logic, ranked by whether it's already causing different behavior or just at risk of it.
- **[`scale-and-sources.md`](./scale-and-sources.md)**: read for launch-readiness review, or to understand what's stub versus real. Three questions answered against the code: can it scale, is demo data swappable for real data, is there one source of truth per concept.
- **[`test-audit.md`](./test-audit.md)**: read to find out where the test suite is weakest before building on it. A line-by-line audit with concrete findings, most already fixed.
- **[`ux-api-review.md`](./ux-api-review.md)**: read before building a client, or deciding what to route next. Whether a good mobile client can be built on the current route surface.
- **[`ux-product-review.md`](./ux-product-review.md)**: read for a product/copy review of the actual user experience. A walkthrough of the app as a first-time user would experience it, with specific copy suggestions for the highest-stakes moments (the payment hold, rejection and restriction messages).

## Elsewhere

- **[`../SPEC.md`](../SPEC.md)**: the original product specification, the ground truth for why a rule exists.
- **[`../INTERFACES.md`](../INTERFACES.md)**: the frozen module-boundary contract from the first build pass.
