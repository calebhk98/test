/**
 * tests/perf/seedScaleCurve.ts, benchmark data generator for
 * tests/perf/scaleCurve.perf.test.ts.
 *
 * PURPOSE: unlike `seedDiscoveryPerf.ts` (which proves cost is flat across
 * viewers in cities of DIFFERENT local density at one FIXED total
 * population), this seeder isolates the other axis the capacity task asks
 * for: does a read path's cost depend on how many users exist ELSEWHERE
 * on the platform, once the viewer's OWN local population is held fixed?
 *
 * To test that honestly, "the viewer's city" must NOT grow when "total
 * users" grows, otherwise a flat-looking local population and a flat
 * total population are the same variable, and the proof is circular. So
 * this seeder fixes `HOME_POPULATION` users in one city (`HOME_CITY`) on
 * every run, and puts the REST of `totalUserCount` in the other, distant
 * cities ("elsewhere"). `HOME_CITY` is Chicago specifically because it is
 * >1,000km from every other seeded city (New York and Philadelphia, at
 * ~130km apart, are too close to each other to safely serve as a fixed
 * "home" against an "elsewhere" that might include the other one), see
 * `seedDiscoveryPerf.ts#CITIES`. All bounding-box radii used by the app
 * default to 160km (`filter.service.ts#DEFAULT_DISCOVERY_RADIUS_KM`), so
 * >1,000km separation means an "elsewhere" user can never land inside the
 * home viewer's geographic box no matter how many are seeded.
 *
 * Every insert is bulk (`unnest` over arrays, chunked) for the same reason
 * `seedDiscoveryPerf.ts` is: seeding tens of thousands of users one row at
 * a time would itself dominate the run.
 */
import { randomUUID } from 'node:crypto';
import type pg from 'pg';
import { CITIES, type City } from './seedDiscoveryPerf.js';

export const HOME_CITY: City = CITIES.find((c) => c.name === 'Chicago')!;
const ELSEWHERE_CITIES: City[] = CITIES.filter((c) => c.name !== 'Chicago');

/** Fixed on every run, regardless of `totalUserCount`, the whole point (see file doc). Comfortably below both `MAX_CANDIDATE_POOL_SIZE` (500) and `DASHBOARD_SCAN_CAP` (5000), so every scale exercises the same EXACT (non-estimator) path, the estimator/truncation path is already covered by `discovery.perf.test.ts`'s New York scenario; this file's job is the population-independence axis, not truncation. */
const HOME_POPULATION = 400;
const MATCH_COUNT = 25;
const MESSAGES_PER_MATCH = 6;
const TIMELINE_MESSAGE_COUNT = 150;
const INTEREST_COUNT = 30;
const CHUNK = 4000;

const GENDERS = ['man', 'woman', 'nonbinary'];

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

function jitter(rng: () => number, center: number, maxDegrees: number): number {
  return center + (rng() - 0.5) * 2 * maxDegrees;
}

interface Insertable {
  id: string;
  latitude: number;
  longitude: number;
}

export interface ScaleCurveSeed {
  totalUserCount: number;
  homeUserCount: number;
  elsewhereUserCount: number;
  viewerId: string;
  candidateId: string;
  matchConversationIds: string[];
  timelineConversationId: string;
}

/** Bulk-inserts `count` users spread across `cities`, each with a profile (completeness fixed well above the discovery gate), an approved primary photo, and a plausible age/gender. Returns just enough to place users geographically and reference them by id. */
async function insertUserBatch(
  pool: pg.Pool,
  rng: () => number,
  count: number,
  cities: City[],
  labelPrefix: string,
): Promise<Insertable[]> {
  const all: Insertable[] = [];
  for (let start = 0; start < count; start += CHUNK) {
    const n = Math.min(CHUNK, count - start);
    const ids: string[] = [];
    const emails: string[] = [];
    const lats: number[] = [];
    const lons: number[] = [];
    const cityNames: string[] = [];
    const ages: number[] = [];
    const genders: string[] = [];
    const displayNames: string[] = [];

    for (let i = 0; i < n; i++) {
      const id = randomUUID();
      const city = cities[Math.floor(rng() * cities.length)]!;
      ids.push(id);
      emails.push(`scalecurve-${labelPrefix}-${start + i}-${id}@test.local`);
      lats.push(jitter(rng, city.lat, 0.5));
      lons.push(jitter(rng, city.lon, 0.5));
      cityNames.push(city.name);
      ages.push(18 + Math.floor(rng() * 47));
      genders.push(GENDERS[Math.floor(rng() * GENDERS.length)]!);
      displayNames.push(`ScaleCurve${labelPrefix}${start + i}`);
      all.push({ id, latitude: lats[i]!, longitude: lons[i]! });
    }

    await pool.query(
      `INSERT INTO users (id, email, password_hash, birthdate, status, last_active_at)
       SELECT id, email, 'x', '1995-01-01', 'active', now() - (floor(random() * 60 * 24 * 14) || ' minutes')::interval
       FROM unnest($1::uuid[], $2::text[]) AS u(id, email)`,
      [ids, emails],
    );

    await pool.query(
      `INSERT INTO profiles (user_id, display_name, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
       SELECT id, dn, city, lat, lon, true, age, gender, 'any', 'long_term', 95
       FROM unnest($1::uuid[], $2::text[], $3::text[], $4::double precision[], $5::double precision[], $6::int[], $7::text[])
         AS t(id, dn, city, lat, lon, age, gender)`,
      [ids, displayNames, cityNames, lats, lons, ages, genders],
    );

    const urls = ids.map((id) => `https://example.test/${id}.jpg`);
    await pool.query(
      `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status)
       SELECT id, url, 0, true, 'approved' FROM unnest($1::uuid[], $2::text[]) AS t(id, url)`,
      [ids, urls],
    );
  }
  return all;
}

/**
 * Seeds `totalUserCount` users total: `HOME_POPULATION` fixed in
 * `HOME_CITY`, the rest spread across the distant `ELSEWHERE_CITIES`. Also
 * wires up a realistic slice of a single home viewer's own activity
 * (matches/messages/interests/filters) so `matches`/`conversation
 * timeline`/`stats` read paths have real, viewer-scoped data to read at
 * every scale, none of which is sized off `totalUserCount`, which is
 * exactly the point: those paths should cost the same at every scale
 * because their own inputs never grow with it.
 */
export async function seedScaleCurveData(pool: pg.Pool, totalUserCount: number, seed = 7): Promise<ScaleCurveSeed> {
  const rng = mulberry32(seed);
  const elsewhereUserCount = Math.max(0, totalUserCount - HOME_POPULATION);

  const homeUsers = await insertUserBatch(pool, rng, HOME_POPULATION, [HOME_CITY], 'home');
  if (elsewhereUserCount > 0) {
    await insertUserBatch(pool, rng, elsewhereUserCount, ELSEWHERE_CITIES, 'else');
  }

  const viewer = homeUsers[0]!;
  const candidate = homeUsers[1]!;

  // ---- matches: MATCH_COUNT conversations between viewer and other home users, each with a few messages ----
  const matchPartnerIds = homeUsers.slice(2, 2 + MATCH_COUNT).map((u) => u.id);
  const { rows: convRows } = await pool.query<{ id: string; user_a_id: string; user_b_id: string }>(
    `INSERT INTO conversations (id, user_a_id, user_b_id, status, created_at, last_message_at)
     SELECT gen_random_uuid(), LEAST($1::uuid, p), GREATEST($1::uuid, p), 'active', now(), now()
     FROM unnest($2::uuid[]) AS p
     RETURNING id, user_a_id, user_b_id`,
    [viewer.id, matchPartnerIds],
  );

  {
    const msgConvIds: string[] = [];
    const msgSenders: string[] = [];
    const msgBodies: string[] = [];
    const msgAgoMinutes: number[] = [];
    for (const conv of convRows) {
      for (let i = 0; i < MESSAGES_PER_MATCH; i++) {
        msgConvIds.push(conv.id);
        msgSenders.push(i % 2 === 0 ? conv.user_a_id : conv.user_b_id);
        msgBodies.push(`seed message ${i}`);
        msgAgoMinutes.push(MESSAGES_PER_MATCH - i);
      }
    }
    await pool.query(
      `INSERT INTO messages (conversation_id, sender_id, body, created_at, read_at)
       SELECT c, s, b, now() - (m || ' minutes')::interval, CASE WHEN m > 2 THEN now() - (m || ' minutes')::interval ELSE NULL END
       FROM unnest($1::uuid[], $2::uuid[], $3::text[], $4::int[]) AS t(c, s, b, m)`,
      [msgConvIds, msgSenders, msgBodies, msgAgoMinutes],
    );
  }

  // ---- one conversation with many messages, for conversation-timeline pagination ----
  const timelinePartner = homeUsers[2 + MATCH_COUNT] ?? homeUsers[2]!;
  const { rows: timelineConvRows } = await pool.query<{ id: string; user_a_id: string; user_b_id: string }>(
    `INSERT INTO conversations (id, user_a_id, user_b_id, status, created_at, last_message_at)
     VALUES (gen_random_uuid(), LEAST($1::uuid, $2::uuid), GREATEST($1::uuid, $2::uuid), 'active', now(), now())
     RETURNING id, user_a_id, user_b_id`,
    [viewer.id, timelinePartner.id],
  );
  const timelineConv = timelineConvRows[0]!;
  {
    const senders: string[] = [];
    const bodies: string[] = [];
    const agoMinutes: number[] = [];
    for (let i = 0; i < TIMELINE_MESSAGE_COUNT; i++) {
      senders.push(i % 2 === 0 ? timelineConv.user_a_id : timelineConv.user_b_id);
      bodies.push(`timeline message ${i}`);
      agoMinutes.push(TIMELINE_MESSAGE_COUNT - i);
    }
    await pool.query(
      `INSERT INTO messages (conversation_id, sender_id, body, created_at, read_at)
       SELECT $1::uuid, s, b, now() - (m || ' minutes')::interval, now() - (m || ' minutes')::interval
       FROM unnest($2::uuid[], $3::text[], $4::int[]) AS t(s, b, m)`,
      [timelineConv.id, senders, bodies, agoMinutes],
    );
  }

  // ---- interests: viewer sends some, receives some (stats funnel/response-behaviour data) ----
  {
    const outgoingTargets = homeUsers.slice(2 + MATCH_COUNT + 1, 2 + MATCH_COUNT + 1 + INTEREST_COUNT / 2).map((u) => u.id);
    const incomingSenders = homeUsers
      .slice(2 + MATCH_COUNT + 1 + INTEREST_COUNT / 2, 2 + MATCH_COUNT + 1 + INTEREST_COUNT)
      .map((u) => u.id);

    if (outgoingTargets.length > 0) {
      await pool.query(
        `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, created_at, expires_at, accepted_at)
         SELECT $1::uuid, r, CASE WHEN random() < 0.4 THEN 'accepted' ELSE 'pending' END, '{}'::jsonb, now(), now() + interval '7 days',
                CASE WHEN random() < 0.4 THEN now() ELSE NULL END
         FROM unnest($2::uuid[]) AS t(r)`,
        [viewer.id, outgoingTargets],
      );
    }
    if (incomingSenders.length > 0) {
      await pool.query(
        `INSERT INTO interests (sender_id, recipient_id, status, policy_snapshot, created_at, expires_at)
         SELECT s, $1::uuid, 'pending', '{}'::jsonb, now(), now() + interval '7 days'
         FROM unnest($2::uuid[]) AS t(s)`,
        [viewer.id, incomingSenders],
      );
    }
  }

  // ---- hard filters for the viewer, so the filter-cost stats path has something to evaluate ----
  await pool.query(
    `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled)
     VALUES ($1, 'age_min', 'gte', '25'::jsonb, true), ($1, 'age_max', 'lte', '45'::jsonb, true), ($1, 'distance_km', 'lte', '160'::jsonb, true)`,
    [viewer.id],
  );

  return {
    totalUserCount,
    homeUserCount: HOME_POPULATION,
    elsewhereUserCount,
    viewerId: viewer.id,
    candidateId: candidate.id,
    matchConversationIds: convRows.map((r) => r.id),
    timelineConversationId: timelineConv.id,
  };
}
