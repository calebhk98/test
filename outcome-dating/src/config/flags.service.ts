import { createHash } from 'node:crypto';
import type { DbClient } from '../db/pool.js';
import type { Logger } from '../lib/logger.js';

/**
 * The §22 feature flag service, backed by `feature_flags` (spec §23.26).
 *
 * Flags support:
 *  - a hard on/off (`enabled`),
 *  - a percentage rollout (`rollout_percent`, 0-100) with **deterministic
 *    per-user bucketing**, the same user always lands in the same bucket
 *    for a given flag, so their experience doesn't flicker between calls,
 *    and rollout can be dialed up without re-bucketing already-included
 *    users,
 *  - segment targeting (`segments`), if non-empty, the caller's segment
 *    list must intersect it.
 *
 * Bucketing: `sha256(flagKey + ":" + userId)`'s first 4 bytes, mod 100.
 * Pure function of (key, userId), no randomness, no DB state, so it's
 * trivially unit-testable and stable across restarts/instances.
 */

/** Flags named explicitly in the spec (§22). Admins may also define ad-hoc flags (§27), so `isEnabled`/`setFlag` accept any string key, these are just typed convenience constants for call sites. */
export const KNOWN_FLAGS = {
  PHOTO_AB_TESTING: 'photo_ab_testing',
  BEHAVIORAL_QUESTION_PROMPTS: 'behavioral_question_prompts',
  NEW_VENUE_CATEGORIES: 'new_venue_categories',
  NEW_REPORT_CATEGORIES: 'new_report_categories',
  CHAT_DECAY: 'chat_decay',
  POST_DATE_FEEDBACK: 'post_date_feedback',
  MILESTONE_BOUNTIES: 'milestone_bounties',
} as const;

export type KnownFlagKey = (typeof KNOWN_FLAGS)[keyof typeof KNOWN_FLAGS];

export interface FeatureFlag {
  key: string;
  enabled: boolean;
  rolloutPercent: number;
  segments: string[];
  updatedAt: Date;
}

/** Per-call targeting context: who's asking, and what segments they belong to (e.g. "beta_testers", "high_trust"). */
export interface FlagEvalContext {
  userId?: string;
  segments?: string[];
}

export function bucketFor(flagKey: string, userId: string): number {
  const digest = createHash('sha256').update(`${flagKey}:${userId}`).digest();
  return digest.readUInt32BE(0) % 100;
}

interface FlagRow {
  key: string;
  enabled: boolean;
  rollout_percent: number;
  segments: string[] | null;
  updated_at: Date;
}

function fromRow(row: FlagRow): FeatureFlag {
  return {
    key: row.key,
    enabled: row.enabled,
    rolloutPercent: row.rollout_percent,
    segments: row.segments ?? [],
    updatedAt: row.updated_at,
  };
}

export class FlagsService {
  private cache = new Map<string, FeatureFlag>();

  constructor(
    private readonly db: DbClient,
    private readonly logger: Logger,
  ) {}

  async getFlag(key: string): Promise<FeatureFlag | undefined> {
    const cached = this.cache.get(key);
    if (cached) return cached;

    const { rows } = await this.db.query<FlagRow>(
      'SELECT key, enabled, rollout_percent, segments, updated_at FROM feature_flags WHERE key = $1',
      [key],
    );
    if (rows.length === 0) return undefined;

    const flag = fromRow(rows[0]!);
    this.cache.set(key, flag);
    return flag;
  }

  async listFlags(): Promise<FeatureFlag[]> {
    const { rows } = await this.db.query<FlagRow>(
      'SELECT key, enabled, rollout_percent, segments, updated_at FROM feature_flags ORDER BY key',
    );
    const flags = rows.map(fromRow);
    for (const f of flags) this.cache.set(f.key, f);
    return flags;
  }

  /**
   * Resolve whether `key` is on for this evaluation context. Unknown flags
   * (no row) default to **off**, a flag must be explicitly created (even
   * disabled) before it can be turned on, so nothing risky ships by
   * accident from a missing seed row.
   */
  async isEnabled(key: string, ctx: FlagEvalContext = {}): Promise<boolean> {
    const flag = await this.getFlag(key);
    if (!flag || !flag.enabled) return false;

    if (flag.segments.length > 0) {
      const userSegments = ctx.segments ?? [];
      if (!flag.segments.some((s) => userSegments.includes(s))) return false;
    }

    if (flag.rolloutPercent >= 100) return true;
    if (flag.rolloutPercent <= 0) return false;

    // A percentage rollout with no stable identity to bucket on cannot be
    // evaluated deterministically; treat as not-enabled rather than random.
    if (!ctx.userId) return false;

    return bucketFor(flag.key, ctx.userId) < flag.rolloutPercent;
  }

  /** Create or update a flag (admin panel, spec §22, §27). Upserts by key. */
  async setFlag(
    key: string,
    patch: { enabled?: boolean; rolloutPercent?: number; segments?: string[] },
  ): Promise<FeatureFlag> {
    const existing = await this.getFlag(key);
    const enabled = patch.enabled ?? existing?.enabled ?? false;
    const rolloutPercent = patch.rolloutPercent ?? existing?.rolloutPercent ?? 0;
    const segments = patch.segments ?? existing?.segments ?? [];

    const { rows } = await this.db.query<FlagRow>(
      `INSERT INTO feature_flags (key, enabled, rollout_percent, segments, updated_at)
       VALUES ($1, $2, $3, $4, now())
       ON CONFLICT (key) DO UPDATE SET
         enabled = EXCLUDED.enabled,
         rollout_percent = EXCLUDED.rollout_percent,
         segments = EXCLUDED.segments,
         updated_at = now()
       RETURNING key, enabled, rollout_percent, segments, updated_at`,
      [key, enabled, rolloutPercent, segments],
    );

    const flag = fromRow(rows[0]!);
    this.cache.set(key, flag);
    this.logger.info('flag.changed', { key, enabled, rolloutPercent, segments });
    return flag;
  }

  invalidate(key?: string): void {
    if (key) this.cache.delete(key);
    else this.cache.clear();
  }

  /** Idempotently insert a disabled, 0%-rollout row for every known flag that doesn't exist yet. */
  async seedKnownFlags(): Promise<void> {
    for (const key of Object.values(KNOWN_FLAGS)) {
      await this.db.query(
        `INSERT INTO feature_flags (key, enabled, rollout_percent, segments, updated_at)
         VALUES ($1, false, 0, '{}', now())
         ON CONFLICT (key) DO NOTHING`,
        [key],
      );
    }
    this.invalidate();
  }
}
