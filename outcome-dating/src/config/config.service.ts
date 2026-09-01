import { z } from 'zod';
import type { DbClient } from '../db/pool.js';
import type { Clock } from '../lib/time.js';
import type { Logger } from '../lib/logger.js';

/**
 * The §21 config service. Business variables (as opposed to deployment env
 * vars, see src/config/env.ts) live in the `config_entries` table
 * (spec §21.1, §23.25) and are read through this service so they can be
 * tuned "without code deployment" (spec §21, Definition of Done #19).
 *
 * Design:
 *  - A typed key registry (`ConfigKeyRegistry`) is the single source of
 *    truth for every key's Zod schema, default value, and semantics. This
 *    gives callers compile-time-checked keys (`ConfigKey`) and
 *    compile-time-checked value types (`ConfigValue<K>`), a typo'd key or
 *    a value of the wrong type is a `tsc` error, not a runtime surprise.
 *  - `scope: 'live'` keys affect objects that don't cache their own copy
 *    (e.g. `chat.active_limit`, spec §21.4 "live"). `scope: 'snapshot'`
 *    keys are ones the spec says existing objects must NOT observe
 *    changing (e.g. `date.escrow_amount_cents`, "existing proposals keep
 *    original"); callers achieve that by calling `snapshotPolicy` at
 *    creation time and storing the result in the object's
 *    `policy_snapshot` jsonb column (spec §21.3), never by re-reading
 *    config later for that object.
 *  - An in-memory cache is invalidated per-key on `set`, and versioned so
 *    staleness is at least detectable.
 */

interface ConfigKeyDef<T> {
  schema: z.ZodType<T>;
  default: T;
  /** "live": current value always applies. "snapshot": existing objects must keep the value in effect when they were created (spec §21.3/§21.4). */
  scope: 'live' | 'snapshot';
  description: string;
  /** Spec section this variable is defined/used in, for traceability. */
  specSection: string;
}

function key<T>(def: ConfigKeyDef<T>): ConfigKeyDef<T> {
  return def;
}

const trustLevel = z.enum(['limited', 'standard', 'trusted', 'elite']);

/**
 * The full key registry. The 13 keys marked "§21.4" are the exact table
 * from the spec and MUST keep these exact keys/defaults. The remaining
 * keys are variables the spec explicitly calls out elsewhere as needing to
 * be configurable (§11.2, §12.3, §14.7, §15.4, §18.5, §18.6, §6.1) but does
 * not tabulate under §21.4, they're included so the rest of the system has
 * one place to source them from, per the "config-driven variables" product
 * decision (spec §33).
 */
export const ConfigKeyRegistry = {
  // ---- §21.4 table (exact) ----
  'interest.outgoing_pending_limit': key({
    schema: z.number().int().min(0),
    default: 5,
    scope: 'live',
    description: 'Max concurrent outgoing pending interests per user.',
    specSection: '§21.4, §11.2',
  }),
  'interest.incoming_pending_limit': key({
    schema: z.number().int().min(0),
    default: 10,
    scope: 'live',
    description: 'Max concurrent incoming pending interests per user (discovery visibility cap).',
    specSection: '§21.4, §11.2, §10.2',
  }),
  'interest.expiry_hours': key({
    schema: z.number().int().positive(),
    default: 48,
    scope: 'snapshot',
    description: 'Hours before a pending interest expires. Existing interests keep the value in effect when sent.',
    specSection: '§21.4, §11.2',
  }),
  'chat.active_limit': key({
    schema: z.number().int().min(0),
    default: 15,
    scope: 'live',
    description: 'Max active (pre-established) conversations per user, used in discovery capacity checks.',
    specSection: '§21.4, §10.2',
  }),
  'chat.date_prompt_hours': key({
    schema: z.number().int().positive(),
    default: 72,
    scope: 'live',
    description: 'Hours after first message with no date proposal before showing the date prompt.',
    specSection: '§21.4, §12.6, §25.3',
  }),
  'chat.pre_date_archive_days': key({
    schema: z.number().int().positive(),
    default: 21,
    scope: 'live',
    description: 'Days after first message with no date proposal before archiving the chat.',
    specSection: '§21.4, §12.6, §25.3',
  }),
  'date.escrow_amount_cents': key({
    schema: z.number().int().min(0),
    default: 2000,
    scope: 'snapshot',
    description: 'Escrow amount per person, in cents. Existing proposals keep the value in effect when created.',
    specSection: '§21.4, §14.1',
  }),
  'date.accept_expiry_hours': key({
    schema: z.number().int().positive(),
    default: 48,
    scope: 'snapshot',
    description: 'Hours the recipient has to accept a date proposal before it expires.',
    specSection: '§21.4, §14.6',
  }),
  'date.full_refund_cutoff_hours': key({
    schema: z.number().int().min(0),
    default: 24,
    scope: 'snapshot',
    description: 'Hours before the scheduled date, above which cancellation is fully refunded.',
    specSection: '§21.4, §14.7',
  }),
  'date.late_cancel_refund_percent': key({
    schema: z.number().int().min(0).max(100),
    default: 0,
    scope: 'snapshot',
    description: 'Refund percent for cancellation inside the full-refund cutoff window.',
    specSection: '§21.4, §14.7',
  }),
  'moderation.auto_restriction_score': key({
    schema: z.number().min(0),
    default: 50,
    scope: 'live',
    description: 'Report/moderation score threshold at which an automated restriction is applied.',
    specSection: '§21.4, §18.5',
  }),
  'moderation.auto_shadowban_score': key({
    schema: z.number().min(0),
    default: 80,
    scope: 'live',
    description: 'Report/moderation score threshold at which an automated shadowban is applied.',
    specSection: '§21.4, §18.5',
  }),
  'trust.link_min_level': key({
    schema: trustLevel,
    default: 'standard' as const,
    scope: 'live',
    description: 'Minimum trust level required for links to be clickable in chat.',
    specSection: '§21.4, §6.4, §19.4',
  }),

  // ---- Additional variables the spec requires be configurable, outside the §21.4 table ----
  'interest.daily_outgoing_limit': key({
    schema: z.number().int().min(0),
    default: 20,
    scope: 'live',
    description: 'Max outgoing interests a user may send per rolling 24h.',
    specSection: '§11.2',
  }),
  'chat.max_messages_per_hour': key({
    schema: z.number().int().min(0),
    default: 120,
    scope: 'live',
    description: 'Max messages a user may send per hour, per conversation participant.',
    specSection: '§12.3',
  }),
  'chat.max_links_per_hour_low_trust': key({
    schema: z.number().int().min(0),
    default: 0,
    scope: 'live',
    description: 'Max clickable external links per hour for Limited-trust users.',
    specSection: '§12.3, §19.4',
  }),
  'chat.max_links_per_hour_standard_trust': key({
    schema: z.number().int().min(0),
    default: 5,
    scope: 'live',
    description: 'Max clickable external links per hour for Standard-trust-and-above users.',
    specSection: '§12.3, §19.4',
  }),
  'date.no_show_refund_percent': key({
    schema: z.number().int().min(0).max(100),
    default: 0,
    scope: 'snapshot',
    description: 'Refund percent when a date is marked no-show.',
    specSection: '§14.7',
  }),
  'date.no_scan_confirmation_hours': key({
    schema: z.number().int().positive(),
    default: 72,
    scope: 'snapshot',
    description: 'Hours after scheduled_end during which both users may confirm attendance if the venue did not scan.',
    specSection: '§15.4',
  }),
  'voucher.expiry_hours_after_date_end': key({
    schema: z.number().int().positive(),
    default: 72,
    scope: 'snapshot',
    description: 'Hours after scheduled_end after which an unredeemed voucher is expired by the voucher-expiry job.',
    specSection: '§25.8',
  }),
  'moderation.auto_suspension_score': key({
    schema: z.number().min(0),
    default: 95,
    scope: 'live',
    description: 'Report/moderation score threshold at which an automated suspension is applied.',
    specSection: '§18.5',
  }),
  'moderation.appeal_cooldown_hours': key({
    schema: z.number().int().min(0),
    default: 24,
    scope: 'live',
    description: 'Minimum hours a restricted/shadowbanned user must wait before submitting an appeal.',
    specSection: '§18.6',
  }),
  'trust.level_standard_min': key({
    schema: z.number().int().min(0).max(100),
    default: 40,
    scope: 'live',
    description: 'Minimum trust_score for the Standard level.',
    specSection: '§6.1',
  }),
  'trust.level_trusted_min': key({
    schema: z.number().int().min(0).max(100),
    default: 70,
    scope: 'live',
    description: 'Minimum trust_score for the Trusted level.',
    specSection: '§6.1',
  }),
  'trust.level_elite_min': key({
    schema: z.number().int().min(0).max(100),
    default: 90,
    scope: 'live',
    description: 'Minimum trust_score for the Elite level.',
    specSection: '§6.1',
  }),

  // ---- Decision-layer additions (see docs/conformance.md's "Open
  // Questions" section, these close gaps flagged in several agents' own
  // module docs as "should be config, but config.service.ts is outside my
  // file-ownership boundary for this pass"; that boundary no longer
  // applies once the decision layer is being applied). ----
  'chat.cooling_days': key({
    schema: z.number().int().positive(),
    default: 14,
    scope: 'live',
    description: 'Days after first message with no date proposal before a conversation moves to "cooling" (the middle §12.6 threshold; date_prompt_hours/pre_date_archive_days already had keys, this one did not).',
    specSection: '§12.6, §25.3',
  }),
  'compatibility.min_shared_questions': key({
    schema: z.number().int().min(0),
    default: 3,
    scope: 'live',
    description: 'Minimum number of questions both users must have fully answered (both sides, both users) before a compatibility score is computed at all; below this the score defaults to compatibility.no_data_default_score.',
    specSection: '§16.2',
  }),
  'compatibility.no_data_default_score': key({
    schema: z.number().min(0).max(1),
    default: 0,
    scope: 'live',
    description: 'Compatibility score (0-1) assigned when too few shared answered questions exist to compute a real one (spec §16.2 "too few shared answered questions", Open Question OQ-2\'s resolution: 0, not neutral).',
    specSection: '§16.2',
  }),
  'discovery.min_profile_completeness': key({
    schema: z.number().int().min(0).max(100),
    default: 50,
    scope: 'live',
    description: 'Minimum profiles.profile_completeness (0-100) for a profile to be discovery-visible (spec §10.2 rule 3).',
    specSection: '§10.2',
  }),
  'interest.outgoing_pending_limit_limited_tier': key({
    schema: z.number().int().min(0),
    default: 2,
    scope: 'live',
    description: 'Outgoing pending interest cap for Limited-trust users specifically (spec §6.4\'s unnumbered "limited" restriction-table cell, Open Question OQ-4\'s resolution). Standard trust and above continue to use interest.outgoing_pending_limit.',
    specSection: '§6.4, §11.2',
  }),
  'trust.expose_raw_score': key({
    schema: z.boolean(),
    default: false,
    scope: 'live',
    description: 'Whether GET /me/trust-shaped responses may surface the exact numeric trustScore rather than trustLevel alone (spec §6.1 "not shown unless product explicitly decides otherwise", Open Question OQ-7\'s resolution: off by default).',
    specSection: '§6.1, §6.3',
  }),
  'date.dispute_auto_resolve_hours': key({
    schema: z.number().int().positive(),
    default: 72,
    scope: 'snapshot',
    description: 'Hours after a date proposal enters `disputed` (itself scheduled_end + no_scan_confirmation_hours) before automated resolution runs: an implicit no-show report is filed against the non-confirming party via report.service, feeding trust recalculation (spec §15.4 "automated handling... according to policy", Open Question OQ-3\'s resolution).',
    specSection: '§15.4, §18.5',
  }),

  // ---- Risk-review remediation (docs/risk-review.md SAF-1/SAF-6/SAF-2) additions ----
  'moderation.minor_suspected_min_corroborating_reporters': key({
    schema: z.number().int().min(1),
    default: 2,
    scope: 'live',
    description: 'Minimum number of DISTINCT, non-clustered, credible reporters who must each independently file a minor_suspected report against the same target before automated SUSPENSION applies. Below this, a fast interim protective action (moderation.minor_suspected_interim_action) applies instead, but the account is never terminated on one uncorroborated report.',
    specSection: 'SAF-1',
  }),
  'moderation.minor_suspected_suspension_score': key({
    schema: z.number().min(0),
    default: 120,
    scope: 'live',
    description: 'Combined credibility-weighted score (see report.service#scoreReport, summed across corroborating minor_suspected reports from credible reporters only) required, together with the corroborating-reporter-count gate above, before automated suspension applies.',
    specSection: 'SAF-1',
  }),
  'moderation.minor_suspected_interim_action': key({
    schema: z.enum(['restriction', 'shadowban']),
    default: 'restriction' as const,
    scope: 'live',
    description: 'Fast, reversible protective action applied immediately on ANY minor_suspected report from a credible reporter, pending corroboration/automated verification, preserves the spec\'s "act immediately" intent without an irreversible-feeling suspension on one unverified signal.',
    specSection: 'SAF-1',
  }),
  'moderation.minor_suspected_reporter_min_account_age_hours': key({
    schema: z.number().min(0),
    default: 24,
    scope: 'live',
    description: 'A reporter\'s account must be at least this old (hours) for their minor_suspected report to count as "credible", excludes a brand-new, just-created account from single-handedly triggering the fast interim action or counting toward suspension corroboration.',
    specSection: 'SAF-1',
  }),
  'moderation.minor_suspected_reporter_credibility_trust_floor': key({
    schema: trustLevel,
    default: 'standard' as const,
    scope: 'live',
    description: 'Minimum trust_level a reporter must hold for their minor_suspected report to count as "credible" (see moderation.minor_suspected_reporter_min_account_age_hours\'s sibling gates).',
    specSection: 'SAF-1',
  }),
  'moderation.minor_suspected_reporter_max_prior_unfounded': key({
    schema: z.number().int().min(0),
    default: 0,
    scope: 'live',
    description: 'A reporter with more than this many of their own past minor_suspected reports marked `outcome = \'unfounded\'` (see report.service#recordReportOutcome) is treated as "previously abusive" and excluded from credibility, their reports still exist and still feed the general moderation score, they just cannot single-handedly trigger the fast interim action or count toward suspension corroboration.',
    specSection: 'SAF-1',
  }),
  'moderation.false_minor_suspected_report_trust_penalty': key({
    schema: z.number().max(0),
    default: -30,
    scope: 'live',
    description: 'Trust-score delta applied to a REPORTER when one of their minor_suspected reports is later marked `outcome = \'unfounded\'` (report.service#recordReportOutcome), the "false reports carry consequences for the reporter" half of the SAF-1 fix.',
    specSection: 'SAF-1',
  }),
  'moderation.brigade_cluster_score_threshold': key({
    schema: z.number().min(0),
    default: 3,
    scope: 'live',
    description: 'Combined weighted-signal score (shared device fingerprint, shared server-observed IP, account-creation-time proximity, report-timing proximity, shared behavioral history with the target, account-graph proximity, see report.service#findClusteredPriorReporters) at/above which two reporters are treated as the same cluster for anti-brigading purposes. Deliberately requires MULTIPLE weak signals, not one, a spoofable client-supplied fingerprint alone (weight 1) can never reach this threshold by itself.',
    specSection: 'SAF-6',
  }),
  'moderation.brigade_account_creation_window_minutes': key({
    schema: z.number().min(0),
    default: 10,
    scope: 'live',
    description: 'Two reporter accounts created within this many minutes of each other contribute the "account creation proximity" signal toward the anti-brigading cluster score (spec §19.2 "suspicious device/IP signals", extended to creation-pattern per the SAF-6 fix).',
    specSection: 'SAF-6',
  }),
  'moderation.brigade_report_timing_window_minutes': key({
    schema: z.number().min(0),
    default: 60,
    scope: 'live',
    description: 'Two reports against the same target filed within this many minutes of each other contribute the "report timing correlation" signal toward the anti-brigading cluster score.',
    specSection: 'SAF-6',
  }),
  'privacy.distance_bucket_km': key({
    schema: z.number().positive(),
    default: 8,
    scope: 'live',
    description: 'Default coarse bucket width (km) for the single shared approximate-distance function (domain/units/distance.ts#approximateDistanceBetween), used by every surface that shows a user their distance to another. A profile\'s own distance_precision_floor_km (if set) can only widen this further for that profile, never narrow it.',
    specSection: 'SAF-2',
  }),
} as const;

export type ConfigKey = keyof typeof ConfigKeyRegistry;
export type ConfigValue<K extends ConfigKey> = z.infer<(typeof ConfigKeyRegistry)[K]['schema']>;

/** Frozen map of every key's default value, typed. Useful for tests/seed. */
export const CONFIG_DEFAULTS: { [K in ConfigKey]: ConfigValue<K> } = Object.fromEntries(
  (Object.keys(ConfigKeyRegistry) as ConfigKey[]).map((k) => [k, ConfigKeyRegistry[k].default]),
) as { [K in ConfigKey]: ConfigValue<K> };

/** Convenience key lists for the two policy snapshots the spec names explicitly (§21.3). */
export const INTEREST_POLICY_KEYS = [
  'interest.expiry_hours',
  'interest.outgoing_pending_limit',
  'interest.incoming_pending_limit',
] as const satisfies readonly ConfigKey[];

export const DATE_PROPOSAL_POLICY_KEYS = [
  'date.escrow_amount_cents',
  'date.accept_expiry_hours',
  'date.full_refund_cutoff_hours',
  'date.late_cancel_refund_percent',
  'date.no_show_refund_percent',
  'date.no_scan_confirmation_hours',
  'date.dispute_auto_resolve_hours',
] as const satisfies readonly ConfigKey[];

type ValuesFor<K extends readonly ConfigKey[]> = { [I in K[number]]: ConfigValue<I> };

interface CacheEntry {
  value: unknown;
  version: number;
}

export class ConfigService {
  private cache = new Map<ConfigKey, CacheEntry>();

  constructor(
    private readonly db: DbClient,
    private readonly clock: Clock,
    private readonly logger: Logger,
  ) {}

  /** Get a single config value, typed by key. Falls back to the registry default if no row exists yet. */
  async get<K extends ConfigKey>(key: K): Promise<ConfigValue<K>> {
    const cached = this.cache.get(key);
    if (cached) return cached.value as ConfigValue<K>;

    const def = ConfigKeyRegistry[key];
    const { rows } = await this.db.query<{ value_json: unknown; version: number }>(
      'SELECT value_json, version FROM config_entries WHERE key = $1',
      [key],
    );

    let value: ConfigValue<K>;
    let version: number;
    if (rows.length > 0) {
      const row = rows[0]!;
      value = def.schema.parse(row.value_json) as ConfigValue<K>;
      version = row.version;
    } else {
      value = def.default as ConfigValue<K>;
      version = 0;
    }

    this.cache.set(key, { value, version });
    return value;
  }

  /** Get several keys at once, typed as an object keyed by the requested keys. */
  async getMany<K extends readonly ConfigKey[]>(keys: K): Promise<ValuesFor<K>> {
    const entries = await Promise.all(keys.map(async (k) => [k, await this.get(k)] as const));
    return Object.fromEntries(entries) as ValuesFor<K>;
  }

  /**
   * Build a §21.3 policy snapshot: the live value of each requested key,
   * captured right now. Callers store the returned object verbatim in the
   * creating row's `policy_snapshot` jsonb column (interests, date
   * proposals) so later config changes never retroactively alter rules for
   * that object, this is what makes `scope: 'snapshot'` keys behave as
   * "existing objects keep original" (spec §21.3, §21.4).
   */
  async snapshotPolicy<K extends readonly ConfigKey[]>(keys: K): Promise<ValuesFor<K>> {
    return this.getMany(keys);
  }

  /**
   * Write a new value for `key`, validating against its schema, bumping
   * `version`, recording `updated_by`/`updated_at`, and logging the change
   * (spec §21.2 "log changes", §28.6 admin audit). Invalidates this
   * process's cache entry immediately; other processes pick it up on their
   * next `get` after their own cache entry (if any) is invalidated,
   * multi-instance cache coherency is out of scope for the MVP in-process
   * cache (see INTERFACES.md invariants).
   */
  async set<K extends ConfigKey>(key: K, value: ConfigValue<K>, updatedBy: string): Promise<void> {
    const def = ConfigKeyRegistry[key];
    const parsed = def.schema.parse(value);

    const { rows } = await this.db.query<{ version: number }>(
      `INSERT INTO config_entries (key, value_json, description, version, updated_by, updated_at)
       VALUES ($1, $2::jsonb, $3, 1, $4, now())
       ON CONFLICT (key) DO UPDATE SET
         value_json = EXCLUDED.value_json,
         version = config_entries.version + 1,
         updated_by = EXCLUDED.updated_by,
         updated_at = now()
       RETURNING version`,
      [key, JSON.stringify(parsed), def.description, updatedBy],
    );

    const version = rows[0]!.version;
    this.cache.set(key, { value: parsed, version });
    this.logger.info('config.changed', { key, version, updatedBy, at: this.clock.now().toISOString() });
  }

  /** Drop cached value(s) so the next `get` re-reads from the DB. Omit `key` to clear the whole cache. */
  invalidate(key?: ConfigKey): void {
    if (key) this.cache.delete(key);
    else this.cache.clear();
  }

  /**
   * Idempotently insert every registry default that doesn't already have a
   * row (ON CONFLICT DO NOTHING, never overwrites an admin-set value).
   * Called by `npm run migrate`'s companion seed step and by tests.
   */
  async seedDefaults(updatedBy = 'system:seed'): Promise<void> {
    for (const k of Object.keys(ConfigKeyRegistry) as ConfigKey[]) {
      const def = ConfigKeyRegistry[k];
      await this.db.query(
        `INSERT INTO config_entries (key, value_json, description, version, updated_by, updated_at)
         VALUES ($1, $2::jsonb, $3, 1, $4, now())
         ON CONFLICT (key) DO NOTHING`,
        [k, JSON.stringify(def.default), def.description, updatedBy],
      );
    }
    this.invalidate();
  }
}
