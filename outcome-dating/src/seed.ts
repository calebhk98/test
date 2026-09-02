/**
 * Deterministic dev/test seed data.
 *
 * Writes directly via SQL rather than through the (stub) service layer,
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
 * design, this is dev/test seed data, not an upsert.
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
import { IMPORTANCE_LEVELS, TAG_INTENSITY_LEVELS } from './domain/questions/index.js';
import type { ImportanceLevel, QuestionTypeDefinition } from './domain/questions/index.js';

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
// THE question bank (redesigned compatibility question system,
// question-system cutover). 65 questions across 9 categories: lifestyle,
// values, relationship_intentions, family, social_energy, health_habits,
// interests, communication, logistics. Written into `question_bank`
// (db/migrations/008_questions.sql).
//
// CUTOVER: this file used to ALSO seed a second, OLDER 26-question, 6-
// category bank (`questions`/`answers`, a flat 1-5 self/partner pair) here
// including `has_children`/`wants_children`/`religion`/`family_closeness`,
// each a duplicate of a concept the typed bank below already covers under
// its own slug (`children_intention`, `religious_practice`,
// `family_closeness` again, the exact collision the product owner
// flagged: "asked users about children and religion three or four
// separate times because each surface defined its own version"). That old
// bank is no longer seeded AT ALL, a fresh install has zero
// `questions`/`answers` rows, so there is nothing left to duplicate
// anything in the typed bank below. See
// src/services/question.service.ts's file-level "CUTOVER" doc for why the
// `questions`/`answers` TABLES themselves still exist in the schema
// (three files outside this build's ownership boundary still depend on
// them) even though nothing here, or anywhere else this build owns,
// writes a row into them anymore.
//
// Every question here picks the type that actually fits its data:
//   - `scale` only where a labelled MIDPOINT is honestly meaningful,
//   - `single_choice` for mutually-exclusive categories (fixes the old
//     "kids: 1-5" bug, see `children_intention` below),
//   - `multi_choice` for pick-any-number questions,
//   - `frequency` for genuinely frequency-shaped habits, with concrete
//     anchors, never a bare 1-5.
// No question text or option label references a section number or any
// spec document, user-visible strings are plain language throughout.
// =====================================================================

function option(key: string, label: string): { key: string; label: string } {
  return { key, label };
}

/** Reused across every `frequency` question so the bank has one consistent, concrete vocabulary rather than a different ad-hoc scale per question. */
const FREQUENCY_ANCHORS = [
  option('never', 'Never'),
  option('yearly', 'A few times a year'),
  option('monthly', 'Monthly'),
  option('weekly', 'Weekly'),
  option('daily', 'Daily'),
];

function frequencyType(): QuestionTypeDefinition {
  return { type: 'frequency', anchors: FREQUENCY_ANCHORS };
}

function scaleType(minLabel: string, maxLabel: string, midLabel: string): QuestionTypeDefinition {
  return { type: 'scale', min: 1, max: 5, minLabel, maxLabel, midLabel };
}

interface NewQuestionSeed {
  slug: string;
  category: string;
  subcategory?: string | null;
  tags?: string[];
  questionText: string;
  typeDef: QuestionTypeDefinition;
  baseWeight: number;
  sensitive?: boolean;
  answerRateHint?: number;
}

const NEW_QUESTION_BANK: NewQuestionSeed[] = [
  // ---- lifestyle (8) ----
  {
    slug: 'smoking_habit',
    category: 'lifestyle',
    questionText: 'Do you smoke?',
    typeDef: { type: 'single_choice', options: [option('no', 'I do not smoke'), option('yes', 'I smoke')] },
    baseWeight: 1.5,
  },
  {
    slug: 'drinking_frequency',
    category: 'lifestyle',
    questionText: 'How often do you drink alcohol?',
    typeDef: frequencyType(),
    baseWeight: 1.0,
  },
  {
    slug: 'recreational_drug_use',
    category: 'lifestyle',
    questionText: 'Do you use recreational drugs?',
    typeDef: { type: 'single_choice', options: [option('no', 'I do not use recreational drugs'), option('yes', 'I use recreational drugs')] },
    baseWeight: 1.3,
    sensitive: true,
  },
  {
    slug: 'sleep_schedule',
    category: 'lifestyle',
    questionText: 'Are you more of a night owl or an early bird?',
    typeDef: scaleType('Night owl, most productive late at night', 'Early bird, most productive at dawn', 'No strong preference either way'),
    baseWeight: 0.6,
  },
  {
    slug: 'tidiness',
    category: 'lifestyle',
    questionText: 'How tidy do you keep your living space?',
    typeDef: scaleType('Comfortable with a lived-in, cluttered space', 'Need everything in its place', 'Tidy in shared spaces, relaxed in private ones'),
    baseWeight: 0.8,
  },
  {
    slug: 'spending_style',
    category: 'lifestyle',
    questionText: 'How would you describe your approach to money?',
    typeDef: scaleType('I spend freely and enjoy the moment', 'I save carefully and plan purchases', 'I balance spending and saving'),
    baseWeight: 1.0,
  },
  {
    slug: 'cooking_frequency',
    category: 'lifestyle',
    questionText: 'How often do you cook a meal from scratch?',
    typeDef: frequencyType(),
    baseWeight: 0.6,
  },
  {
    slug: 'living_situation',
    category: 'lifestyle',
    questionText: 'What is your current living situation?',
    typeDef: {
      type: 'single_choice',
      options: [option('alone', 'I live alone'), option('roommates', 'I live with roommates'), option('family', 'I live with family'), option('partner', 'I live with a partner')],
    },
    baseWeight: 0.5,
  },

  // ---- values (7) ----
  {
    slug: 'religious_practice',
    category: 'values',
    questionText: 'How central is religion to your daily life?',
    typeDef: scaleType('Not religious at all', 'Religion guides most of my daily life', 'Religion matters to me but is not central'),
    baseWeight: 1.4,
    sensitive: true,
  },
  {
    slug: 'political_engagement',
    category: 'values',
    questionText: 'How politically engaged are you?',
    typeDef: scaleType('I rarely follow or discuss politics', 'I follow and engage with politics closely', 'I stay informed but do not engage deeply'),
    baseWeight: 0.7,
    sensitive: true,
  },
  {
    slug: 'monogamy_structure',
    category: 'values',
    questionText: 'What relationship structure are you looking for?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('monogamous', 'Monogamous only'),
        option('open_to_enm', 'Open to ethical non-monogamy'),
        option('polyamorous', 'Polyamorous'),
        option('still_figuring_out', 'Still figuring out what works for me'),
      ],
    },
    baseWeight: 1.8,
    sensitive: true,
  },
  {
    slug: 'honesty_directness',
    category: 'values',
    questionText: 'How direct are you when something is bothering you?',
    typeDef: scaleType('I lead with warmth and soften hard truths', 'I lead with directness, even when it is blunt', 'I adjust my directness to the situation'),
    baseWeight: 0.7,
  },
  {
    slug: 'environmental_values',
    category: 'values',
    questionText: 'How much does sustainability shape your everyday choices?',
    typeDef: scaleType('Sustainability rarely factors into my choices', 'Sustainability strongly shapes my choices', 'I consider it sometimes, without being strict'),
    baseWeight: 0.6,
  },
  {
    slug: 'life_priorities',
    category: 'values',
    questionText: 'What matters most to you right now? Choose all that apply.',
    typeDef: {
      type: 'multi_choice',
      options: [
        option('career_growth', 'Career growth'),
        option('family', 'Family'),
        option('personal_growth', 'Personal growth'),
        option('financial_security', 'Financial security'),
        option('creativity', 'Creativity'),
        option('adventure', 'Adventure'),
        option('community', 'Community involvement'),
      ],
    },
    baseWeight: 0.9,
  },
  {
    slug: 'conflict_style',
    category: 'values',
    questionText: 'When a disagreement comes up, what is your instinct?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('talk_immediately', 'I want to talk it through right away'),
        option('need_time', 'I need time alone before I can talk it through'),
        option('avoid', 'I tend to avoid conflict altogether'),
        option('depends', 'It depends on the situation'),
      ],
    },
    baseWeight: 1.0,
  },

  // ---- relationship_intentions (7) ----
  {
    slug: 'relationship_goal',
    category: 'relationship_intentions',
    questionText: 'What are you looking for right now?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('casual', 'Casual dating, no particular destination'),
        option('long_term', 'A long-term committed relationship'),
        option('marriage', 'Marriage'),
        option('not_sure', 'Not sure yet, open to seeing what happens'),
      ],
    },
    baseWeight: 1.8,
  },
  {
    slug: 'relationship_pace',
    category: 'relationship_intentions',
    questionText: 'How do you like a new relationship to progress?',
    typeDef: scaleType('I prefer to take things slowly', 'I prefer to move quickly once I feel a connection', 'I let the relationship set its own pace'),
    baseWeight: 1.0,
  },
  {
    slug: 'exclusivity_timing',
    category: 'relationship_intentions',
    questionText: 'When do you like to define exclusivity?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('early', 'I like to define it early'),
        option('after_a_while', 'I prefer to wait a while before defining it'),
        option('mutual_conversation', 'I wait until it comes up naturally in conversation'),
      ],
    },
    baseWeight: 0.9,
  },
  {
    slug: 'cohabitation_timeline',
    category: 'relationship_intentions',
    questionText: 'When would you consider moving in with a partner?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('not_interested', 'Not interested in living together'),
        option('after_engagement', 'Only after getting engaged or married'),
        option('when_it_feels_right', 'Whenever it feels right, no set timeline'),
        option('sooner_than_most', 'Sooner than most, if things are going well'),
      ],
    },
    baseWeight: 1.0,
  },
  {
    slug: 'marriage_intention',
    category: 'relationship_intentions',
    questionText: 'Is marriage something you want?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('want_marriage', 'I want to get married'),
        option('open_not_required', 'Open to marriage, but it is not required'),
        option('do_not_want_marriage', 'I do not want to get married'),
        option('undecided', 'Undecided'),
      ],
    },
    baseWeight: 1.3,
  },
  {
    slug: 'long_distance_openness',
    category: 'relationship_intentions',
    questionText: 'How open are you to a long-distance relationship?',
    typeDef: scaleType('Not open to long-distance at all', 'Comfortable with long-distance for as long as it takes', 'Open to it for a limited time'),
    baseWeight: 0.6,
  },
  {
    slug: 'dating_multiple_people',
    category: 'relationship_intentions',
    questionText: 'Before things are exclusive, how do you approach dating?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('exclusive_only', 'I only date one person at a time'),
        option('casually_dating_multiple', 'I am comfortable casually dating more than one person until exclusive'),
      ],
    },
    baseWeight: 0.8,
  },

  // ---- family (7) ----
  {
    slug: 'children_intention',
    category: 'family',
    questionText: 'Where are you on having children?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('no_kids_no_want', 'No children, and do not want any'),
        option('no_kids_want', 'No children, but want them'),
        option('has_kids_want_more', 'Have children, and want more'),
        option('has_kids_no_more', 'Have children, and do not want more'),
        option('still_deciding', 'Still deciding'),
      ],
    },
    baseWeight: 2.0,
  },
  {
    slug: 'children_timeline',
    category: 'family',
    questionText: 'If you want children (or more children), what is your timeline?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('as_soon_as_possible', 'As soon as possible'),
        option('within_a_few_years', 'Within the next few years'),
        option('someday_not_soon', 'Someday, but not soon'),
        option('not_applicable', 'Not applicable to me'),
      ],
    },
    baseWeight: 1.0,
  },
  {
    slug: 'family_closeness',
    category: 'family',
    questionText: 'How close are you with your family?',
    typeDef: scaleType('Not close with my family', 'Extremely close with my family', 'Moderately close, in touch regularly'),
    baseWeight: 0.7,
  },
  {
    slug: 'family_holiday_expectations',
    category: 'family',
    questionText: 'How much do holidays revolve around family for you?',
    typeDef: scaleType('I rarely spend holidays with family', 'Holidays with family are non-negotiable for me', 'I split holidays between family and other plans'),
    baseWeight: 0.5,
  },
  {
    slug: 'coparenting_style',
    category: 'family',
    subcategory: 'parenting',
    questionText: 'If you have or plan to have children, what is your parenting style?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('very_structured', 'A very structured, scheduled parenting style'),
        option('flexible', 'A flexible, go-with-the-flow parenting style'),
        option('not_applicable', 'Not applicable to me'),
      ],
    },
    baseWeight: 0.6,
  },
  {
    slug: 'blended_family_openness',
    category: 'family',
    questionText: 'How open are you to dating someone who already has children?',
    typeDef: scaleType('Not open to dating someone with children', 'Very open to dating someone with children', 'Open to it, would need to get to know the situation'),
    baseWeight: 1.1,
  },
  {
    slug: 'pet_family_role',
    category: 'family',
    questionText: 'What role do pets play in your idea of family?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('no_pets_not_interested', 'No pets, and not interested in having any'),
        option('no_pets_want_some', 'No pets, but would like some'),
        option('have_pets', 'I have pets and consider them family'),
      ],
    },
    baseWeight: 0.7,
  },

  // ---- social_energy (6), fixes the old "no coherent scale" bug: real
  // behavioural frequency/scale anchors, not a mood rating.
  {
    slug: 'recharge_frequency',
    category: 'social_energy',
    questionText: 'How often do you spend a full evening alone to recharge?',
    typeDef: frequencyType(),
    baseWeight: 0.8,
  },
  {
    slug: 'party_departure_style',
    category: 'social_energy',
    questionText: 'At a party or gathering, how long do you usually stay?',
    typeDef: scaleType('I usually leave within the first hour', 'I usually stay until the very end', 'I usually stay a few hours, then head out'),
    baseWeight: 0.6,
  },
  {
    slug: 'plans_with_friends_frequency',
    category: 'social_energy',
    questionText: 'How often do you make plans with friends?',
    typeDef: frequencyType(),
    baseWeight: 0.6,
  },
  {
    slug: 'large_gatherings_comfort',
    category: 'social_energy',
    questionText: 'How do large gatherings affect your energy?',
    typeDef: scaleType('Large gatherings drain me quickly', 'Large gatherings energize me', 'I enjoy them for a while, then need a break'),
    baseWeight: 0.7,
  },
  {
    slug: 'initiating_plans',
    category: 'social_energy',
    questionText: 'In your friendships, who usually initiates plans?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('usually_me', 'I am usually the one who initiates'),
        option('usually_others', 'Others usually initiate with me'),
        option('about_even', 'It is about even'),
      ],
    },
    baseWeight: 0.4,
  },
  {
    slug: 'solo_travel_comfort',
    category: 'social_energy',
    questionText: 'How comfortable are you traveling alone?',
    typeDef: scaleType('I would not travel alone', 'I regularly travel alone and enjoy it', 'I am comfortable with it occasionally'),
    baseWeight: 0.5,
  },

  // ---- health_habits (8) ----
  {
    slug: 'exercise_frequency',
    category: 'health_habits',
    questionText: 'How often do you exercise?',
    typeDef: frequencyType(),
    baseWeight: 0.9,
  },
  {
    slug: 'diet_style',
    category: 'health_habits',
    questionText: 'Do you follow any particular diet?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('no_restrictions', 'No dietary restrictions'),
        option('vegetarian', 'Vegetarian'),
        option('vegan', 'Vegan'),
        option('pescatarian', 'Pescatarian'),
        option('other_restriction', 'Other dietary restriction'),
      ],
    },
    baseWeight: 0.5,
  },
  {
    slug: 'sleep_hours',
    category: 'health_habits',
    questionText: 'How many hours do you usually sleep a night?',
    typeDef: scaleType('Usually fewer than 6 hours a night', 'Usually 9 or more hours a night', 'Usually around 7 to 8 hours a night'),
    baseWeight: 0.6,
  },
  {
    slug: 'mental_health_openness',
    category: 'health_habits',
    questionText: 'How openly do you talk about mental health?',
    typeDef: scaleType('I prefer to keep mental health private', 'I am very open about discussing mental health', 'I will discuss it once I feel comfortable'),
    baseWeight: 0.7,
    sensitive: true,
  },
  {
    slug: 'therapy_experience',
    category: 'health_habits',
    questionText: 'What is your experience with therapy?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('currently_in_therapy', 'Currently in therapy'),
        option('have_done_therapy', 'Have done therapy in the past'),
        option('open_not_currently', 'Open to it, not currently in therapy'),
        option('not_for_me', 'Not something I am interested in'),
      ],
    },
    baseWeight: 0.5,
    sensitive: true,
  },
  {
    slug: 'substance_free_dating',
    category: 'health_habits',
    questionText: 'How important is dating substance-free to you?',
    typeDef: {
      type: 'single_choice',
      options: [option('important_to_me', 'Dating substance-free is important to me'), option('not_a_priority', 'Not a priority either way')],
    },
    baseWeight: 0.8,
    sensitive: true,
  },
  {
    slug: 'outdoor_activity_frequency',
    category: 'health_habits',
    questionText: 'How often do you spend time outdoors (hiking, walking, sports)?',
    typeDef: frequencyType(),
    baseWeight: 0.6,
  },
  {
    slug: 'screen_time',
    category: 'health_habits',
    questionText: 'How would you describe your screen time outside of work?',
    typeDef: scaleType('Very low screen time outside of work', 'High screen time, including gaming or scrolling', 'Moderate screen time'),
    baseWeight: 0.5,
  },

  // ---- interests (7) ----
  {
    slug: 'languages_spoken',
    category: 'interests',
    questionText: 'Which languages do you speak? Choose all that apply.',
    typeDef: {
      type: 'multi_choice',
      options: [
        option('english', 'English'),
        option('spanish', 'Spanish'),
        option('french', 'French'),
        option('mandarin', 'Mandarin'),
        option('hindi', 'Hindi'),
        option('arabic', 'Arabic'),
        option('portuguese', 'Portuguese'),
        option('german', 'German'),
        option('japanese', 'Japanese'),
        option('other_language', 'Another language'),
      ],
    },
    baseWeight: 0.4,
  },
  {
    slug: 'weekend_activities',
    category: 'interests',
    questionText: 'What do you usually do on weekends? Choose all that apply.',
    typeDef: {
      type: 'multi_choice',
      options: [
        option('hiking', 'Hiking'),
        option('cooking', 'Cooking'),
        option('gaming', 'Gaming'),
        option('reading', 'Reading'),
        option('live_music', 'Live music'),
        option('museums', 'Museums'),
        option('sports', 'Playing or watching sports'),
        option('board_games', 'Board games'),
        option('travel', 'Traveling'),
        option('volunteering', 'Volunteering'),
      ],
    },
    baseWeight: 0.5,
  },
  {
    slug: 'music_taste',
    category: 'interests',
    questionText: 'What kinds of music do you enjoy? Choose all that apply.',
    typeDef: {
      type: 'multi_choice',
      options: [
        option('pop', 'Pop'),
        option('rock', 'Rock'),
        option('hip_hop', 'Hip hop'),
        option('electronic', 'Electronic'),
        option('classical', 'Classical'),
        option('jazz', 'Jazz'),
        option('country', 'Country'),
        option('indie', 'Indie'),
        option('world_music', 'World music'),
      ],
    },
    baseWeight: 0.3,
  },
  {
    slug: 'reading_frequency',
    category: 'interests',
    questionText: 'How often do you read for pleasure?',
    typeDef: frequencyType(),
    baseWeight: 0.4,
  },
  {
    slug: 'creative_hobby_involvement',
    category: 'interests',
    questionText: 'How big a part of your life are creative hobbies (art, music, writing, etc.)?',
    typeDef: scaleType('I rarely make time for creative hobbies', 'Creative hobbies are a big part of my life', 'I dabble in creative hobbies now and then'),
    baseWeight: 0.4,
  },
  {
    slug: 'sports_fandom',
    category: 'interests',
    questionText: 'How much do you follow sports?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('avid_fan', 'Avid fan, I follow regularly'),
        option('casual_fan', 'Casual fan, I watch occasionally'),
        option('not_a_fan', 'Not into sports'),
      ],
    },
    baseWeight: 0.3,
  },
  {
    slug: 'travel_frequency',
    category: 'interests',
    questionText: 'How often do you travel somewhere new?',
    typeDef: frequencyType(),
    baseWeight: 0.6,
  },

  // ---- communication (7) ----
  {
    slug: 'texting_frequency_expectation',
    category: 'communication',
    questionText: 'How much texting do you expect while getting to know someone?',
    typeDef: scaleType('I am fine with infrequent texting between dates', 'I like frequent texting throughout the day', 'A check-in once or twice a day feels right'),
    baseWeight: 0.8,
  },
  {
    slug: 'love_language',
    category: 'communication',
    questionText: 'How do you most like to give and receive affection? Choose all that apply.',
    typeDef: {
      type: 'multi_choice',
      options: [
        option('words_of_affirmation', 'Words of affirmation'),
        option('quality_time', 'Quality time'),
        option('acts_of_service', 'Acts of service'),
        option('physical_touch', 'Physical touch'),
        option('gifts', 'Thoughtful gifts'),
      ],
    },
    baseWeight: 0.9,
  },
  {
    slug: 'conflict_resolution_timing',
    category: 'communication',
    questionText: 'When there is a disagreement, when do you want to talk about it?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('address_immediately', 'Right away'),
        option('need_a_cooldown', 'After a cooldown period'),
        option('varies', 'It depends on the situation'),
      ],
    },
    baseWeight: 0.9,
  },
  {
    slug: 'phone_call_comfort',
    category: 'communication',
    questionText: 'How do you feel about phone calls versus texting?',
    typeDef: scaleType('I avoid phone calls, I prefer texting', 'I much prefer calling over texting', 'I am comfortable with either'),
    baseWeight: 0.4,
  },
  {
    slug: 'public_affection_comfort',
    category: 'communication',
    questionText: 'How comfortable are you with public displays of affection?',
    typeDef: scaleType('I prefer to avoid public displays of affection', 'I am very comfortable with public affection', 'A little is fine, nothing excessive'),
    baseWeight: 0.6,
  },
  {
    slug: 'directness_receiving_feedback',
    category: 'communication',
    questionText: 'How do you like to receive feedback from a partner?',
    typeDef: scaleType('Delivered gently, with cushioning', 'Delivered directly, no cushioning', 'Depends on the topic'),
    baseWeight: 0.5,
  },
  {
    slug: 'social_media_sharing',
    category: 'communication',
    questionText: 'How openly do you share your relationships on social media?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('very_private', 'I keep my relationships off social media'),
        option('occasional_posts', 'I post occasionally about my relationship'),
        option('openly_share', 'I openly share my relationship on social media'),
      ],
    },
    baseWeight: 0.4,
  },

  // ---- logistics (8) ----
  {
    slug: 'max_travel_distance_for_dates',
    category: 'logistics',
    questionText: 'How far are you willing to travel for a date?',
    typeDef: scaleType('I prefer to stay within a short distance', 'I am happy to travel a long way for the right person', 'I am comfortable with a moderate distance'),
    baseWeight: 0.5,
  },
  {
    slug: 'work_schedule',
    category: 'logistics',
    questionText: 'What does your typical work schedule look like?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('standard_hours', 'Standard daytime hours'),
        option('nights_or_shifts', 'Nights or rotating shifts'),
        option('flexible_remote', 'Flexible or remote schedule'),
        option('irregular_freelance', 'Irregular freelance schedule'),
      ],
    },
    baseWeight: 0.5,
  },
  {
    slug: 'relocation_openness',
    category: 'logistics',
    questionText: 'How open are you to relocating for a relationship?',
    typeDef: scaleType('Not open to relocating for a relationship', 'Very open to relocating for the right relationship', 'Open to it under the right circumstances'),
    baseWeight: 0.9,
  },
  {
    slug: 'car_ownership',
    category: 'logistics',
    questionText: 'How do you usually get around?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('own_a_car', 'I own a car'),
        option('no_car_use_transit', 'No car, I rely on public transit or rideshare'),
        option('no_car_walk_bike', 'No car, I mostly walk or bike'),
      ],
    },
    baseWeight: 0.3,
  },
  {
    slug: 'financial_merging_expectation',
    category: 'logistics',
    questionText: 'In a serious relationship, how do you expect finances to work?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('keep_fully_separate', 'Keep finances fully separate'),
        option('merge_some', 'Merge some shared expenses, keep the rest separate'),
        option('merge_fully', 'Merge finances fully'),
        option('not_sure', 'Not sure yet'),
      ],
    },
    baseWeight: 1.0,
  },
  {
    slug: 'date_planning_style',
    category: 'logistics',
    questionText: 'When it comes to planning a date, what do you prefer?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('i_like_to_plan', 'I like to plan the details myself'),
        option('prefer_spontaneous', 'I prefer spontaneous, unplanned dates'),
        option('happy_either_way', 'Happy either way'),
      ],
    },
    baseWeight: 0.4,
  },
  {
    slug: 'schedule_flexibility',
    category: 'logistics',
    questionText: 'How flexible is your schedule for seeing someone?',
    typeDef: scaleType('My schedule is fixed and hard to change', 'My schedule is very flexible', 'Somewhat flexible, with some fixed commitments'),
    baseWeight: 0.5,
  },
  {
    slug: 'preferred_date_time',
    category: 'logistics',
    questionText: 'When do you most prefer to go on dates?',
    typeDef: {
      type: 'single_choice',
      options: [
        option('weekday_evenings', 'Weekday evenings'),
        option('weekend_daytime', 'Weekend daytime'),
        option('weekend_evenings', 'Weekend evenings'),
        option('flexible_anytime', 'Flexible, anytime works'),
      ],
    },
    baseWeight: 0.3,
  },
];

/**
 * Generates a plausible (selfValue, preferenceValue) pair for one typed
 * question, matching the exact shapes typeHandlers.ts validates
 * (src/domain/questions/typeHandlers.ts), a scalar for scale/frequency/
 * single_choice-self, a set for single_choice-preference/multi_choice.
 * Seed data bypasses the zod/service validation path for speed (like the
 * rest of this file), so staying shape-correct here matters.
 */
function randomAnswerValuesForType(typeDef: QuestionTypeDefinition): { selfValue: unknown; preferenceValue: unknown } {
  switch (typeDef.type) {
    case 'scale':
      return { selfValue: randInt(typeDef.min, typeDef.max), preferenceValue: randInt(typeDef.min, typeDef.max) };
    case 'frequency':
      return { selfValue: pick(typeDef.anchors).key, preferenceValue: pick(typeDef.anchors).key };
    case 'single_choice': {
      const selfValue = pick(typeDef.options).key;
      const acceptableCount = randInt(1, Math.min(3, typeDef.options.length));
      const preferenceValue = shuffle(typeDef.options).slice(0, acceptableCount).map((o) => o.key);
      return { selfValue, preferenceValue };
    }
    case 'multi_choice': {
      const selfCount = randInt(0, typeDef.options.length);
      const prefCount = randInt(0, typeDef.options.length);
      const selfValue = shuffle(typeDef.options).slice(0, selfCount).map((o) => o.key);
      const preferenceValue = shuffle(typeDef.options).slice(0, prefCount).map((o) => o.key);
      return { selfValue, preferenceValue };
    }
  }
}

// =====================================================================
// Interest tags (§8.4), a mix, some naturally stigma-prone (good for
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
// §13.2 venues, 8 across the category list.
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


/** The trust band a score falls in. Derived here rather than picked, because the database enforces that the two agree. */
function trustLevelForScore(score: number): 'limited' | 'standard' | 'trusted' | 'elite' {
  if (score >= 90) return 'elite';
  if (score >= 70) return 'trusted';
  if (score >= 40) return 'standard';
  return 'limited';
}

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

  // CUTOVER: the OLD 26-question bank (`questions` table) is no longer
  // seeded at all, see this file's file-level CUTOVER note above and
  // question.service.ts's for why the table still exists in the schema
  // but is deliberately left empty by every fresh seed.
  console.log('Seeding question bank...');
  const newBank: Array<{ id: string; slug: string; typeDef: QuestionTypeDefinition; sensitive: boolean }> = [];
  for (const q of NEW_QUESTION_BANK) {
    const { rows } = await pool.query<{ id: string }>(
      `INSERT INTO question_bank
         (slug, version, is_current, category, subcategory, tags, question_type, question_text, type_definition, base_weight, sensitive, active, answer_rate_hint)
       VALUES ($1, 1, true, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, true, $10)
       RETURNING id`,
      [
        q.slug,
        q.category,
        q.subcategory ?? null,
        q.tags ?? [],
        q.typeDef.type,
        q.questionText,
        JSON.stringify(q.typeDef),
        q.baseWeight,
        q.sensitive ?? false,
        q.answerRateHint ?? 0.5,
      ],
    );
    newBank.push({ id: rows[0]!.id, slug: q.slug, typeDef: q.typeDef, sensitive: q.sensitive ?? false });
  }
  console.log(`  ${newBank.length} new-bank questions across ${new Set(NEW_QUESTION_BANK.map((q) => q.category)).size} categories`);

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

    const trustScore = randInt(45, 95);
    const { rows: userRows } = await pool.query<{ id: string }>(
      `INSERT INTO users (email, password_hash, birthdate, status, trust_score, trust_level, shadowbanned, suspended, email_verified_at)
       VALUES ($1,$2,$3,'active',$4,$5,false,false, now())
       RETURNING id`,
      [email, passwordHash, birthdate.toISOString().slice(0, 10), trustScore, trustLevelForScore(trustScore)],
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

    // CUTOVER: no OLD-bank answers are seeded (see file-level CUTOVER
    // note), every seeded answer below is against the ONE typed bank.

    // Tags: 2-5 tags per user, mostly public, sometimes private_reciprocal.
    const userTagIds = shuffle(tagIds).slice(0, randInt(2, 5));
    for (const tagId of userTagIds) {
      const visibility = rng() < 0.25 ? 'private_reciprocal' : 'public';
      await pool.query(
        `INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1,$2,$3)`,
        [userId, tagId, visibility],
      );
    }

    // Tag intensity: roughly half of the tags a user holds get an
    // intensity ("I bake" daily vs. once a quarter are different).
    for (const tagId of userTagIds) {
      if (rng() < 0.5) {
        await pool.query(
          `INSERT INTO user_tag_intensity (user_id, tag_id, intensity) VALUES ($1,$2,$3)`,
          [userId, tagId, pick(TAG_INTENSITY_LEVELS)],
        );
      }
    }

    // Avoid tags: a minority of users avoid 1-2 tags they don't hold
    // themselves ("do not show me people who list astrology").
    if (rng() < 0.3) {
      const avoidCandidates = tagIds.filter((id) => !userTagIds.includes(id));
      const avoidTagIds = shuffle(avoidCandidates).slice(0, randInt(1, 2));
      for (const tagId of avoidTagIds) {
        await pool.query(`INSERT INTO user_avoid_tags (user_id, tag_id) VALUES ($1,$2)`, [userId, tagId]);
      }
    }

    // New-bank answers: a subset of the 65 questions, mixing every status
    // (answered / skipped / prefer_not_to_say) and every importance level
    // (including irrelevant and deal_breaker) so the new scoring/selector/
    // deal-breaker paths have realistic data to exercise. Users answer a
    // SMALL subset, per the task brief, not the whole bank.
    const questionsToTouch = shuffle(newBank).slice(0, randInt(20, 40));
    for (const q of questionsToTouch) {
      const roll = rng();
      // Sensitive questions get "prefer not to say" noticeably more often.
      const preferNotToSayThreshold = q.sensitive ? 0.18 : 0.05;
      if (roll < preferNotToSayThreshold) {
        await pool.query(
          `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, answered_at, updated_at)
           VALUES ($1, $2, $3, 'prefer_not_to_say', now(), now())`,
          [userId, q.slug, q.id],
        );
        continue;
      }
      if (roll < preferNotToSayThreshold + 0.1) {
        await pool.query(
          `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, answered_at, updated_at)
           VALUES ($1, $2, $3, 'skipped', now(), now())`,
          [userId, q.slug, q.id],
        );
        continue;
      }

      const { selfValue, preferenceValue } = randomAnswerValuesForType(q.typeDef);
      const importance: ImportanceLevel = pick(IMPORTANCE_LEVELS);
      await pool.query(
        `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
         VALUES ($1, $2, $3, 'answered', $4::jsonb, $5::jsonb, $6, now(), now())`,
        [userId, q.slug, q.id, JSON.stringify(selfValue), JSON.stringify(preferenceValue), importance],
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
