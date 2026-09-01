/**
 * Deterministic dev/test seed data.
 *
 * Writes directly via SQL rather than through the (stub) service layer —
 * every `src/services/*.service.ts` body throws `NotImplementedError`
 * until parallel agents fill them in, so this script can't depend on them.
 * It seeds exactly the rows those agents' bodies and the smoke test need:
 * config defaults, feature flags, the §8 question bank, interest tags,
 * §13.2 venues, and ~20 realistic users with profiles/photos/answers/
 * filters/tags.
 *
 * Fully deterministic: a fixed-seed PRNG (mulberry32) drives every random
 * choice, so re-running `npm run seed` against a fresh DB always produces
 * byte-identical data. Idempotent-ish: seeding twice against the same DB
 * without a reset will fail on unique constraints (email, slug, ...) by
 * design — this is dev/test seed data, not an upsert.
 *
 * Usage: `npm run seed` (run migrations first: `npm run migrate`).
 */
import { getPool, closePool } from './db/pool.js';
import { runMigrations } from './db/migrate.js';
import { ConfigService } from './config/config.service.js';
import { FlagsService } from './config/flags.service.js';
import { SystemClock } from './lib/time.js';
import { createLogger } from './lib/logger.js';
import { hashPassword } from './lib/hash.js';

// ---- deterministic PRNG (mulberry32) ----
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

const rng = mulberry32(42);
function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(rng() * arr.length)]!;
}
function randInt(min: number, max: number): number {
  return min + Math.floor(rng() * (max - min + 1));
}
function shuffle<T>(arr: readonly T[]): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    const tmp = copy[i]!;
    copy[i] = copy[j]!;
    copy[j] = tmp!;
  }
  return copy;
}

// =====================================================================
// §8 question bank — 26 questions across 6 categories.
// =====================================================================
interface QuestionSeed {
  slug: string;
  category: string;
  questionText: string;
  selfLeftLabel: string;
  selfRightLabel: string;
  partnerLeftLabel: string;
  partnerRightLabel: string;
  weight: number;
  polarity: 'standard' | 'reversed';
  sensitive: boolean;
}

const QUESTIONS: QuestionSeed[] = [
  // lifestyle
  { slug: 'pets', category: 'lifestyle', questionText: 'Pets', selfLeftLabel: 'I do not like pets', selfRightLabel: 'I have pets / love pets', partnerLeftLabel: 'I do not want my partner to have pets', partnerRightLabel: 'Partner must love/have pets', weight: 1.0, polarity: 'standard', sensitive: false },
  { slug: 'smoking', category: 'lifestyle', questionText: 'Smoking', selfLeftLabel: 'I do not smoke', selfRightLabel: 'I smoke regularly', partnerLeftLabel: 'Partner must not smoke', partnerRightLabel: "Smoking doesn't bother me", weight: 1.5, polarity: 'reversed', sensitive: false },
  { slug: 'drinking', category: 'lifestyle', questionText: 'Drinking', selfLeftLabel: 'I do not drink', selfRightLabel: 'I drink regularly', partnerLeftLabel: 'Partner should not drink', partnerRightLabel: 'Partner drinks socially or more', weight: 1.0, polarity: 'standard', sensitive: false },
  { slug: 'drug_use', category: 'lifestyle', questionText: 'Recreational drug use', selfLeftLabel: 'I never use', selfRightLabel: 'I use regularly', partnerLeftLabel: 'Partner must never use', partnerRightLabel: "Doesn't bother me", weight: 1.3, polarity: 'reversed', sensitive: true },
  { slug: 'fitness', category: 'lifestyle', questionText: 'Fitness / exercise', selfLeftLabel: 'Rarely exercise', selfRightLabel: 'Exercise daily', partnerLeftLabel: 'Fitness not important in partner', partnerRightLabel: 'Partner must be very active', weight: 0.8, polarity: 'standard', sensitive: false },
  { slug: 'early_late', category: 'lifestyle', questionText: 'Sleep schedule', selfLeftLabel: 'Night owl', selfRightLabel: 'Early bird', partnerLeftLabel: 'Prefer a night owl partner', partnerRightLabel: 'Prefer an early bird partner', weight: 0.5, polarity: 'standard', sensitive: false },

  // family
  { slug: 'has_children', category: 'family', questionText: 'Do you have children', selfLeftLabel: 'No children', selfRightLabel: 'Have children', partnerLeftLabel: 'Partner must not have children', partnerRightLabel: 'Fine if partner has children', weight: 1.5, polarity: 'standard', sensitive: false },
  { slug: 'wants_children', category: 'family', questionText: 'Do you want children', selfLeftLabel: 'Do not want children', selfRightLabel: 'Definitely want children', partnerLeftLabel: 'Partner must not want children', partnerRightLabel: 'Partner must want children', weight: 2.0, polarity: 'standard', sensitive: false },
  { slug: 'family_closeness', category: 'family', questionText: 'Closeness with family', selfLeftLabel: 'Not close with family', selfRightLabel: 'Very close with family', partnerLeftLabel: 'Family closeness not important', partnerRightLabel: 'Partner must be close with family', weight: 0.7, polarity: 'standard', sensitive: false },

  // values
  { slug: 'religion', category: 'values', questionText: 'Religious practice', selfLeftLabel: 'Not religious', selfRightLabel: 'Very religious', partnerLeftLabel: 'Partner should not be religious', partnerRightLabel: 'Partner must share my faith', weight: 1.4, polarity: 'standard', sensitive: true },
  { slug: 'politics', category: 'values', questionText: 'Political engagement', selfLeftLabel: 'Not politically engaged', selfRightLabel: 'Very politically engaged', partnerLeftLabel: "Partner's politics don't matter", partnerRightLabel: 'Partner must share my politics', weight: 0.9, polarity: 'standard', sensitive: true },
  { slug: 'financial_style', category: 'values', questionText: 'Spending vs. saving', selfLeftLabel: 'Free spender', selfRightLabel: 'Careful saver', partnerLeftLabel: 'Prefer a free-spending partner', partnerRightLabel: 'Prefer a careful-saving partner', weight: 1.1, polarity: 'standard', sensitive: false },
  { slug: 'honesty_directness', category: 'values', questionText: 'Directness in communication', selfLeftLabel: 'Very indirect/gentle', selfRightLabel: 'Very direct/blunt', partnerLeftLabel: 'Prefer a gentle partner', partnerRightLabel: 'Prefer a direct partner', weight: 0.8, polarity: 'standard', sensitive: false },
  { slug: 'monogamy', category: 'values', questionText: 'Relationship structure', selfLeftLabel: 'Open to non-monogamy', selfRightLabel: 'Strictly monogamous', partnerLeftLabel: 'Open to non-monogamy', partnerRightLabel: 'Must be strictly monogamous', weight: 1.8, polarity: 'standard', sensitive: true },

  // habits
  { slug: 'cleanliness', category: 'habits', questionText: 'Tidiness', selfLeftLabel: 'Messy', selfRightLabel: 'Very tidy', partnerLeftLabel: "Messiness doesn't bother me", partnerRightLabel: 'Partner must be very tidy', weight: 0.7, polarity: 'standard', sensitive: false },
  { slug: 'cooking', category: 'habits', questionText: 'Cooking at home', selfLeftLabel: 'Never cook', selfRightLabel: 'Cook most meals', partnerLeftLabel: "Cooking doesn't matter", partnerRightLabel: 'Partner should love cooking', weight: 0.6, polarity: 'standard', sensitive: false },
  { slug: 'screen_time', category: 'habits', questionText: 'Screen time / gaming', selfLeftLabel: 'Very low screen time', selfRightLabel: 'High screen time / avid gamer', partnerLeftLabel: 'Prefer low screen time partner', partnerRightLabel: "Screen time doesn't matter", weight: 0.6, polarity: 'standard', sensitive: false },
  { slug: 'spontaneity', category: 'habits', questionText: 'Planning vs. spontaneity', selfLeftLabel: 'Meticulous planner', selfRightLabel: 'Very spontaneous', partnerLeftLabel: 'Prefer a planner partner', partnerRightLabel: 'Prefer a spontaneous partner', weight: 0.7, polarity: 'standard', sensitive: false },

  // social
  { slug: 'introversion', category: 'social', questionText: 'Introvert vs. extrovert', selfLeftLabel: 'Strong introvert', selfRightLabel: 'Strong extrovert', partnerLeftLabel: 'Prefer an introverted partner', partnerRightLabel: 'Prefer an extroverted partner', weight: 0.9, polarity: 'standard', sensitive: false },
  { slug: 'social_circle_overlap', category: 'social', questionText: 'Merging friend groups', selfLeftLabel: 'Keep circles separate', selfRightLabel: 'Love merging friend groups', partnerLeftLabel: 'Prefer separate circles', partnerRightLabel: 'Want merged friend groups', weight: 0.4, polarity: 'standard', sensitive: false },
  { slug: 'humor_style', category: 'social', questionText: 'Sense of humor', selfLeftLabel: 'Dry / sarcastic', selfRightLabel: 'Silly / goofy', partnerLeftLabel: 'Prefer dry/sarcastic humor', partnerRightLabel: 'Prefer silly/goofy humor', weight: 0.5, polarity: 'standard', sensitive: false },
  { slug: 'affection_style', category: 'social', questionText: 'Physical affection', selfLeftLabel: 'Low affection', selfRightLabel: 'Very affectionate', partnerLeftLabel: 'Prefer low affection partner', partnerRightLabel: 'Partner must be very affectionate', weight: 1.0, polarity: 'standard', sensitive: false },

  // activity / relationship intention
  { slug: 'hiking', category: 'activity', questionText: 'Hiking / outdoors', selfLeftLabel: 'Not outdoorsy', selfRightLabel: 'Avid hiker/outdoors person', partnerLeftLabel: "Outdoorsiness doesn't matter", partnerRightLabel: 'Partner must love the outdoors', weight: 0.6, polarity: 'standard', sensitive: false },
  { slug: 'travel', category: 'activity', questionText: 'Travel frequency', selfLeftLabel: 'Rarely travel', selfRightLabel: 'Travel constantly', partnerLeftLabel: 'Prefer a homebody partner', partnerRightLabel: 'Partner must love to travel', weight: 0.7, polarity: 'standard', sensitive: false },
  { slug: 'nightlife', category: 'activity', questionText: 'Going out / nightlife', selfLeftLabel: 'Prefer staying in', selfRightLabel: 'Love going out', partnerLeftLabel: 'Prefer a homebody partner', partnerRightLabel: 'Partner must love going out', weight: 0.6, polarity: 'standard', sensitive: false },
  { slug: 'relationship_pace', category: 'activity', questionText: 'Relationship pace', selfLeftLabel: 'Prefer taking things slow', selfRightLabel: 'Prefer moving quickly', partnerLeftLabel: 'Want a partner who takes it slow', partnerRightLabel: 'Want a partner who moves quickly', weight: 1.0, polarity: 'standard', sensitive: false },
  { slug: 'long_term_intent', category: 'activity', questionText: 'Long-term seriousness', selfLeftLabel: 'Casual dating only', selfRightLabel: 'Looking for marriage', partnerLeftLabel: 'Want a casual partner', partnerRightLabel: 'Want a marriage-minded partner', weight: 1.6, polarity: 'standard', sensitive: false },
];

// =====================================================================
// Interest tags (§8.4) — a mix, some naturally stigma-prone (good for
// exercising private/reciprocal visibility once that path is implemented).
// =====================================================================
const INTEREST_TAGS: Array<{ name: string; category: string; publicDescription: string }> = [
  { name: 'Hiking', category: 'outdoors', publicDescription: 'Enjoys hiking and trails' },
  { name: 'Board games', category: 'hobbies', publicDescription: 'Enjoys tabletop and board games' },
  { name: 'Anime', category: 'hobbies', publicDescription: 'Enjoys anime and manga' },
  { name: 'Live music', category: 'culture', publicDescription: 'Enjoys concerts and live music' },
  { name: 'Cooking', category: 'lifestyle', publicDescription: 'Enjoys cooking' },
  { name: 'Yoga', category: 'fitness', publicDescription: 'Practices yoga' },
  { name: 'Rock climbing', category: 'fitness', publicDescription: 'Enjoys rock climbing' },
  { name: 'Reading', category: 'hobbies', publicDescription: 'Avid reader' },
  { name: 'Photography', category: 'creative', publicDescription: 'Enjoys photography' },
  { name: 'Video games', category: 'hobbies', publicDescription: 'Enjoys video games' },
  { name: 'Travel', category: 'lifestyle', publicDescription: 'Loves to travel' },
  { name: 'Volunteering', category: 'community', publicDescription: 'Enjoys volunteering' },
  { name: 'Wine tasting', category: 'lifestyle', publicDescription: 'Enjoys wine tasting' },
  { name: 'Astrology', category: 'lifestyle', publicDescription: 'Interested in astrology' },
  { name: 'Comedy shows', category: 'culture', publicDescription: 'Enjoys stand-up comedy' },
];

// =====================================================================
// §13.2 venues — 8 across the category list.
// =====================================================================
const VENUES: Array<{
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  category: string;
  marginPercent: number;
  redemptionMethod: 'qr_scan' | 'manual_code';
}> = [
  { name: 'Daily Grind Coffee', address: '100 Main St, Springfield', latitude: 39.78, longitude: -89.65, category: 'coffee', marginPercent: 15, redemptionMethod: 'qr_scan' },
  { name: 'Sweet Tooth Dessert Bar', address: '210 Elm St, Springfield', latitude: 39.79, longitude: -89.64, category: 'dessert', marginPercent: 18, redemptionMethod: 'qr_scan' },
  { name: 'The Copper Still', address: '55 River Rd, Springfield', latitude: 39.80, longitude: -89.66, category: 'drinks', marginPercent: 20, redemptionMethod: 'qr_scan' },
  { name: 'Riverside Walk & Overlook', address: 'Riverside Park, Springfield', latitude: 39.77, longitude: -89.63, category: 'walk', marginPercent: 0, redemptionMethod: 'manual_code' },
  { name: 'City Art Museum', address: '400 Museum Way, Springfield', latitude: 39.81, longitude: -89.62, category: 'museum', marginPercent: 12, redemptionMethod: 'qr_scan' },
  { name: 'Pixel Palace Arcade', address: '88 Arcade Ave, Springfield', latitude: 39.76, longitude: -89.67, category: 'arcade', marginPercent: 22, redemptionMethod: 'qr_scan' },
  { name: 'The Blue Note Lounge', address: '12 Jazz Ln, Springfield', latitude: 39.82, longitude: -89.61, category: 'live_music', marginPercent: 25, redemptionMethod: 'qr_scan' },
  { name: 'Laugh Track Comedy Club', address: '77 Comedy Ct, Springfield', latitude: 39.75, longitude: -89.68, category: 'comedy', marginPercent: 20, redemptionMethod: 'qr_scan' },
];

const FIRST_NAMES = [
  'Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Jamie', 'Avery',
  'Quinn', 'Drew', 'Sam', 'Reese', 'Skyler', 'Dakota', 'Rowan', 'Emerson',
  'Hayden', 'Parker', 'Blake', 'Charlie', 'Elliot', 'Finley',
];
const CITIES = ['Springfield', 'Rivertown', 'Lakeside', 'Hillcrest', 'Brookfield'];
const GENDERS = ['woman', 'man', 'nonbinary'] as const;
const INTENTIONS = ['long_term', 'short_term', 'open_to_either'];

const USER_COUNT = 20;

async function main(): Promise<void> {
  console.log('Running migrations...');
  await runMigrations();

  const pool = getPool();
  const clock = new SystemClock();
  const logger = createLogger({ service: 'seed' });
  const config = new ConfigService(pool, clock, logger);
  const flags = new FlagsService(pool, logger);

  console.log('Seeding config defaults...');
  await config.seedDefaults('system:seed');

  console.log('Seeding feature flags...');
  await flags.seedKnownFlags();

  console.log('Seeding question bank...');
  const questionIds: string[] = [];
  for (const q of QUESTIONS) {
    const { rows } = await pool.query<{ id: string }>(
      `INSERT INTO questions
         (slug, category, question_text, self_left_label, self_right_label, partner_left_label, partner_right_label, weight, polarity, sensitive, active)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,true)
       RETURNING id`,
      [q.slug, q.category, q.questionText, q.selfLeftLabel, q.selfRightLabel, q.partnerLeftLabel, q.partnerRightLabel, q.weight, q.polarity, q.sensitive],
    );
    questionIds.push(rows[0]!.id);
  }
  console.log(`  ${questionIds.length} questions`);

  console.log('Seeding interest tags...');
  const tagIds: string[] = [];
  for (const t of INTEREST_TAGS) {
    const { rows } = await pool.query<{ id: string }>(
      `INSERT INTO interest_tags (name, category, public_description) VALUES ($1,$2,$3) RETURNING id`,
      [t.name, t.category, t.publicDescription],
    );
    tagIds.push(rows[0]!.id);
  }
  console.log(`  ${tagIds.length} interest tags`);

  console.log('Seeding venues...');
  let venueCount = 0;
  for (const v of VENUES) {
    const timeSlotConfig = {
      slots: [
        { dayOfWeek: 5, startMinute: 17 * 60, endMinute: 21 * 60 },
        { dayOfWeek: 6, startMinute: 12 * 60, endMinute: 21 * 60 },
        { dayOfWeek: 0, startMinute: 12 * 60, endMinute: 18 * 60 },
      ],
    };
    await pool.query(
      `INSERT INTO venues (name, address, latitude, longitude, category, active, margin_percent, time_slot_config, redemption_method)
       VALUES ($1,$2,$3,$4,$5,true,$6,$7::jsonb,$8)`,
      [v.name, v.address, v.latitude, v.longitude, v.category, v.marginPercent, JSON.stringify(timeSlotConfig), v.redemptionMethod],
    );
    venueCount++;
  }
  console.log(`  ${venueCount} venues`);

  console.log('Seeding users...');
  const passwordHash = await hashPassword('SeedPassw0rd!');
  const userIds: string[] = [];

  for (let i = 0; i < USER_COUNT; i++) {
    const firstName = FIRST_NAMES[i % FIRST_NAMES.length]!;
    const email = `${firstName.toLowerCase()}${i}@seed.outcome-dating.test`;
    const ageYears = randInt(21, 45);
    const birthdate = new Date();
    birthdate.setFullYear(birthdate.getFullYear() - ageYears);
    birthdate.setMonth(randInt(0, 11), randInt(1, 28));

    const { rows: userRows } = await pool.query<{ id: string }>(
      `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at)
       VALUES ($1,$2,$3,'active',$4,$5,false,false, now())
       RETURNING id`,
      [email, passwordHash, birthdate.toISOString().slice(0, 10), randInt(45, 95), pick(['standard', 'standard', 'trusted', 'limited', 'elite'])],
    );
    const userId = userRows[0]!.id;
    userIds.push(userId);

    const gender = pick(GENDERS);
    const seeking = pick(GENDERS);
    const city = pick(CITIES);

    await pool.query(
      `INSERT INTO profiles (user_id, display_name, bio, city, latitude, longitude, location_fuzzed, age, gender, seeking, relationship_intention, profile_completeness)
       VALUES ($1,$2,$3,$4,$5,$6,true,$7,$8,$9,$10,$11)`,
      [
        userId,
        firstName,
        `Hi, I'm ${firstName}. Seed profile bio number ${i}.`,
        city,
        39.7 + rng() * 0.2,
        -89.7 + rng() * 0.2,
        ageYears,
        gender,
        seeking,
        pick(INTENTIONS),
        randInt(40, 100),
      ],
    );

    // Photos: 1-4 per user, first is primary.
    const photoCount = randInt(1, 4);
    for (let p = 0; p < photoCount; p++) {
      await pool.query(
        `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected, blur_score, brightness_score, group_photo_detected, perceptual_hash)
         VALUES ($1,$2,$3,$4,'approved',true,$5,$6,false,$7)`,
        [
          userId,
          `https://seed.outcome-dating.test/photos/${userId}/${p}.jpg`,
          p,
          p === 0,
          rng() * 0.3,
          0.4 + rng() * 0.4,
          `seed_${userId}_${p}`,
        ],
      );
    }

    // Hard filters: age range + max distance always; a few optional ones.
    const ageMin = Math.max(18, ageYears - randInt(3, 10));
    const ageMax = ageYears + randInt(3, 10);
    await pool.query(
      `INSERT INTO hard_filters (user_id, filter_key, operator, value, enabled) VALUES
         ($1,'age_min','gte',$2::jsonb,true),
         ($1,'age_max','lte',$3::jsonb,true),
         ($1,'distance_km','lte',$4::jsonb,true)`,
      [userId, JSON.stringify(ageMin), JSON.stringify(ageMax), JSON.stringify(randInt(10, 100))],
    );

    // Answers: answer 15-22 of the 26 questions.
    const answeredQuestions = shuffle(questionIds).slice(0, randInt(15, 22));
    for (const questionId of answeredQuestions) {
      const selfValue = randInt(1, 5);
      const partnerValue = randInt(1, 5);
      await pool.query(
        `INSERT INTO answers (user_id, question_id, self_value, partner_value) VALUES ($1,$2,$3,$4)`,
        [userId, questionId, selfValue, partnerValue],
      );
    }

    // Tags: 2-5 tags per user, mostly public, sometimes private_reciprocal.
    const userTagIds = shuffle(tagIds).slice(0, randInt(2, 5));
    for (const tagId of userTagIds) {
      const visibility = rng() < 0.25 ? 'private_reciprocal' : 'public';
      await pool.query(
        `INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1,$2,$3)`,
        [userId, tagId, visibility],
      );
    }
  }
  console.log(`  ${userIds.length} users`);

  console.log('Seed complete.');
}

const isMain = process.argv[1]?.endsWith('seed.ts') || process.argv[1]?.endsWith('seed.js');
if (isMain) {
  main()
    .then(() => closePool())
    .catch(async (err) => {
      console.error(err);
      await closePool();
      process.exit(1);
    });
}

export { main as seed };
