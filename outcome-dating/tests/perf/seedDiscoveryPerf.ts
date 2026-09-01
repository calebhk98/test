/**
 * tests/perf/seedDiscoveryPerf.ts — benchmark data generator for
 * tests/perf/discovery.perf.test.ts.
 *
 * Builds a "realistic" dataset per the task brief: tens of thousands of
 * users spread across several distinct cities (so the geographic bound
 * this build adds is actually exercised, not vacuous), with varied hard
 * filters and answered questions (so filter evaluation and compatibility
 * scoring are exercised too, not just the candidate-pool query alone).
 *
 * Every insert here is BULK (`unnest` over arrays, chunked), never a
 * per-row round trip — seeding 20,000+ users one row at a time would
 * itself take longer than the thing this build fixed. This file exists
 * purely to make a benchmark dataset fast; it is not part of the
 * production code path and intentionally does not reuse
 * discovery.service.ts/filter.service.ts's own (deliberately different)
 * query shapes.
 */
import { randomUUID } from 'node:crypto';
import type pg from 'pg';

export interface City {
  name: string;
  lat: number;
  lon: number;
}

/** Six real, geographically distant metro areas — far enough apart that a ~160km default search radius around one never reaches another. */
export const CITIES: City[] = [
  { name: 'New York', lat: 40.7128, lon: -74.006 },
  { name: 'Los Angeles', lat: 34.0522, lon: -118.2437 },
  { name: 'Chicago', lat: 41.8781, lon: -87.6298 },
  { name: 'Houston', lat: 29.7604, lon: -95.3698 },
  { name: 'Phoenix', lat: 33.4484, lon: -112.074 },
  { name: 'Philadelphia', lat: 39.9526, lon: -75.1652 },
];

const GENDERS = ['man', 'woman', 'nonbinary'];
const RELATIONSHIP_INTENTIONS = ['long_term', 'short_term', 'casual', 'friendship'];
const BODY_TYPES = ['slim', 'athletic', 'average', 'curvy', 'muscular', 'plus_size', 'other'];

function pick<T>(rng: () => number, arr: readonly T[]): T {
  return arr[Math.floor(rng() * arr.length)]!;
}

/** Deterministic, seedable PRNG (mulberry32) — reproducible benchmark runs across machines/CI, no external dependency. */
function mulberry32(seed: number): () => number {
  let a = seed;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** ~1 degree of latitude/longitude jitter is on the order of 0-110km — spreads users across (and sometimes just past) a single metro's usual search radius, which is the point: some same-city users should still fall outside a viewer's default radius, some cross-city users should not (they never do at these distances, but the jitter still exercises the box's edges honestly). */
function jitter(rng: () => number, center: number, maxDegrees: number): number {
  return center + (rng() - 0.5) * 2 * maxDegrees;
}

export interface SeededUser {
  id: string;
  city: City;
  latitude: number;
  longitude: number;
}

export interface SeedResult {
  users: SeededUser[];
  questionIds: string[];
}

/**
 * Seeds `userCount` users spread across `CITIES`, each with a profile, an
 * approved primary photo (~90% of users — the rest exercise the "no
 * approved photo" gate), a random subset of `questionCount` answered
 * questions, and hard filters on a realistic fraction of users
 * (age range, distance, gender preference). Returns enough to pick a
 * "viewer" and reason about expected pool sizes.
 */
export async function seedDiscoveryPerfData(
  pool: pg.Pool,
  opts: { userCount: number; questionCount?: number; seed?: number },
): Promise<SeedResult> {
  const rng = mulberry32(opts.seed ?? 42);
  const questionCount = opts.questionCount ?? 10;

  // ---- questions (shared question bank) ----
  const questionIds: string[] = [];
  {
    const ids: string[] = [];
    const slugs: string[] = [];
    for (let i = 0; i < questionCount; i++) {
      ids.push(randomUUID());
      slugs.push(`perf-q-${i}`);
    }
    await pool.query(
      `INSERT INTO questions (id, slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
       SELECT id, slug, 'perf', slug, 'l', 'r', 'l', 'r', 1 + (row_number() OVER ())::float / 10, 'standard', false, true
       FROM unnest($1::uuid[], $2::text[]) AS t(id, slug)`,
      [ids, slugs],
    );
    questionIds.push(...ids);
  }

  // ---- users + profiles + photos + filters + answers, chunked ----
  const CHUNK = 2000;
  const users: SeededUser[] = [];

  for (let start = 0; start < opts.userCount; start += CHUNK) {
    const end = Math.min(start + CHUNK, opts.userCount);
    const n = end - start;

    const userIds: string[] = [];
    const emails: string[] = [];
    const lastActiveOffsets: number[] = []; // minutes ago
    const chunkUsers: SeededUser[] = [];

    for (let i = 0; i < n; i++) {
      const id = randomUUID();
      const city = pick(rng, CITIES);
      const lat = jitter(rng, city.lat, 0.9); // up to ~100km spread within/around the metro
      const lon = jitter(rng, city.lon, 0.9);
      userIds.push(id);
      emails.push(`perf-${start + i}-${id}@test.local`);
      lastActiveOffsets.push(Math.floor(rng() * 60 * 24 * 14)); // within the last 14 days
      chunkUsers.push({ id, city, latitude: lat, longitude: lon });
    }

    await pool.query(
      `INSERT INTO users (id, email, password_hash, birthdate, status, last_active_at)
       SELECT u.id, u.email, 'x', '1995-01-01', 'active', now() - (u.minutes_ago || ' minutes')::interval
       FROM unnest($1::uuid[], $2::text[], $3::int[]) AS u(id, email, minutes_ago)`,
      [userIds, emails, lastActiveOffsets],
    );

    const displayNames: string[] = [];
    const cityNames: string[] = [];
    const lats: number[] = [];
    const lons: number[] = [];
    const ages: number[] = [];
    const genders: string[] = [];
    const relIntents: string[] = [];
    const completenesses: number[] = [];
    const heights: number[] = [];
    const weights: number[] = [];
    const bodyTypes: string[] = [];

    for (let i = 0; i < n; i++) {
      displayNames.push(`PerfUser${start + i}`);
      cityNames.push(chunkUsers[i]!.city.name);
      lats.push(chunkUsers[i]!.latitude);
      lons.push(chunkUsers[i]!.longitude);
      ages.push(18 + Math.floor(rng() * 47));
      genders.push(pick(rng, GENDERS));
      relIntents.push(pick(rng, RELATIONSHIP_INTENTIONS));
      completenesses.push(70 + Math.floor(rng() * 30));
      heights.push(150 + Math.floor(rng() * 50));
      weights.push(50000 + Math.floor(rng() * 60000));
      bodyTypes.push(pick(rng, BODY_TYPES));
    }

    await pool.query(
      `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness, height_cm, weight_g, body_type)
       SELECT id, display_name, city, lat, lon, true, age, gender, 'any', rel, completeness, height_cm, weight_g, body_type
       FROM unnest($1::uuid[], $2::text[], $3::text[], $4::double precision[], $5::double precision[], $6::int[], $7::text[], $8::text[], $9::int[], $10::int[], $11::int[], $12::text[])
         AS t(id, display_name, city, lat, lon, age, gender, rel, completeness, height_cm, weight_g, body_type)`,
      [userIds, displayNames, cityNames, lats, lons, ages, genders, relIntents, completenesses, heights, weights, bodyTypes],
    );

    // ~90% get an approved primary photo.
    const photoUserIds = userIds.filter(() => rng() < 0.9);
    if (photoUserIds.length > 0) {
      const urls = photoUserIds.map((id) => `https://example.test/${id}.jpg`);
      await pool.query(
        `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status)
         SELECT id, url, 0, true, 'approved' FROM unnest($1::uuid[], $2::text[]) AS t(id, url)`,
        [photoUserIds, urls],
      );
    }

    // Hard filters: ~30% age range, ~25% distance, ~15% gender preference.
    const filterOwners: string[] = [];
    const filterKeys: string[] = [];
    const filterOps: string[] = [];
    const filterValues: string[] = [];
    for (let i = 0; i < n; i++) {
      const id = userIds[i]!;
      if (rng() < 0.3) {
        filterOwners.push(id, id);
        filterKeys.push('age_min', 'age_max');
        filterOps.push('gte', 'lte');
        const lo = 20 + Math.floor(rng() * 20);
        filterValues.push(String(lo), String(lo + 10 + Math.floor(rng() * 20)));
      }
      if (rng() < 0.25) {
        filterOwners.push(id);
        filterKeys.push('distance_km');
        filterOps.push('lte');
        filterValues.push(String(10 + Math.floor(rng() * 190)));
      }
      if (rng() < 0.15) {
        filterOwners.push(id);
        filterKeys.push('gender_preference');
        filterOps.push('eq');
        filterValues.push(JSON.stringify(pick(rng, GENDERS)));
      }
    }
    if (filterOwners.length > 0) {
      await pool.query(
        `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled)
         SELECT owner, key, op, val::jsonb, true
         FROM unnest($1::uuid[], $2::text[], $3::text[], $4::text[]) AS t(owner, key, op, val)`,
        [filterOwners, filterKeys, filterOps, filterValues],
      );
    }

    // Answers: each user answers a random subset of the question bank.
    const ansUsers: string[] = [];
    const ansQuestions: string[] = [];
    const ansSelf: number[] = [];
    const ansPartner: number[] = [];
    for (let i = 0; i < n; i++) {
      const id = userIds[i]!;
      const answerCount = Math.floor(rng() * (questionIds.length + 1));
      const shuffled = [...questionIds].sort(() => rng() - 0.5).slice(0, answerCount);
      for (const qId of shuffled) {
        ansUsers.push(id);
        ansQuestions.push(qId);
        ansSelf.push(1 + Math.floor(rng() * 5));
        ansPartner.push(1 + Math.floor(rng() * 5));
      }
    }
    if (ansUsers.length > 0) {
      // Answers can be large per chunk; sub-chunk to keep any one query's
      // parameter arrays a reasonable size.
      const ANSWER_CHUNK = 20_000;
      for (let a = 0; a < ansUsers.length; a += ANSWER_CHUNK) {
        const sliceEnd = Math.min(a + ANSWER_CHUNK, ansUsers.length);
        await pool.query(
          `INSERT INTO answers (user_id, question_id, self_value, partner_value)
           SELECT u, q, s, p FROM unnest($1::uuid[], $2::uuid[], $3::int[], $4::int[]) AS t(u, q, s, p)`,
          [ansUsers.slice(a, sliceEnd), ansQuestions.slice(a, sliceEnd), ansSelf.slice(a, sliceEnd), ansPartner.slice(a, sliceEnd)],
        );
      }
    }

    users.push(...chunkUsers);
  }

  return { users, questionIds };
}
