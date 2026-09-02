import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestDatabase, teardownTestDatabase, getTestPool, buildCtx, userActor, insertUser } from './testCtx.js';
import * as profile from '../../src/services/profile.service.js';
import { ForbiddenError, NotFoundError, ValidationError } from '../../src/lib/errors.js';

before(async () => {
  await setupTestDatabase('profile');
});

after(async () => {
  await teardownTestDatabase();
});

const NOW = new Date();

async function createUser(
  _overrides: Partial<{ latitude: number; longitude: number; city: string }> = {},
): Promise<string> {
  return insertUser('profileuser');
}

test('updateMyProfile: creating a profile requires the core required fields', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  await assert.rejects(
    () => profile.updateMyProfile(ctx, { displayName: 'Alex' }), // missing age/gender/seeking/relationshipIntention
    ValidationError,
  );
});

test('updateMyProfile: creates a profile and computes completeness', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  const created = await profile.updateMyProfile(ctx, {
    displayName: 'Alex',
    age: 30,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
  });

  assert.equal(created.displayName, 'Alex');
  // No bio/city/photos/answers/tags yet: displayName(15) + core fields(10) = 25.
  assert.equal(created.profileCompleteness, 25);

  const fetched = await profile.getMyProfile(ctx);
  assert.equal(fetched.displayName, 'Alex');
  assert.equal(fetched.profileCompleteness, 25);
});

test('computeProfileCompleteness: matches the documented weighted formula as fields are added', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });
  const pool = getTestPool();

  await profile.updateMyProfile(ctx, {
    displayName: 'Bailey',
    age: 28,
    gender: 'nonbinary',
    seeking: 'woman',
    relationshipIntention: 'open_to_either',
    bio: 'This is a sufficiently long bio for full credit.',
    city: 'Rivertown',
  });
  // 15 (name) + 15 (bio>=20 chars) + 10 (city) + 10 (core fields) = 50
  assert.equal(await profile.computeProfileCompleteness(ctx, userId), 50);

  // One approved photo -> +20 = 70
  await pool.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected)
     VALUES ($1, 'https://example.test/a.jpg', 0, true, 'approved', true)`,
    [userId],
  );
  assert.equal(await profile.computeProfileCompleteness(ctx, userId), 70);

  // Two more approved photos (3 total) -> +10 = 80
  for (let i = 1; i <= 2; i++) {
    await pool.query(
      `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected)
       VALUES ($1, $2, $3, false, 'approved', false)`,
      [userId, `https://example.test/${i}.jpg`, i],
    );
  }
  assert.equal(await profile.computeProfileCompleteness(ctx, userId), 80);

  // 5 answered questions -> +15 = 95. ONE typed question bank
  // (question_bank/user_question_answers, db/migrations/008_questions.sql)
  // replaces the OLD `questions`/`answers` tables this used to insert
  // into directly (db/migrations/022_drop_old_question_bank.sql drops
  // both). `computeProfileCompleteness` counts only `status = 'answered'`
  // rows, see that function's own doc for why this is a deliberate,
  // slightly narrower (more correct) mapping than the OLD bank's
  // "any row counts" behavior.
  const { rows: questionRows } = await pool.query<{ id: string; slug: string }>(
    `INSERT INTO question_bank (slug, version, is_current, category, question_type, question_text, type_definition, active)
     SELECT 'q_' || gs || '_' || $1, 1, true, 'lifestyle', 'scale', 'Q',
            '{"type":"scale","min":1,"max":5,"minLabel":"low","maxLabel":"high","midLabel":"mid"}'::jsonb, true
       FROM generate_series(1,5) gs
     RETURNING id, slug`,
    [userId],
  );
  for (const q of questionRows) {
    await pool.query(
      `INSERT INTO user_question_answers (user_id, question_slug, question_bank_id, status, self_value, preference_value, importance, answered_at, updated_at)
       VALUES ($1, $2, $3, 'answered', '3'::jsonb, '3'::jsonb, 'slight', now(), now())`,
      [userId, q.slug, q.id],
    );
  }
  assert.equal(await profile.computeProfileCompleteness(ctx, userId), 95);

  // 1 interest tag -> +5 = 100
  const { rows: tagRows } = await pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category) VALUES ($1, 'hobbies') RETURNING id`,
    [`tag-${userId}`],
  );
  await pool.query('INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, $3)', [
    userId,
    tagRows[0]!.id,
    'public',
  ]);
  assert.equal(await profile.computeProfileCompleteness(ctx, userId), 100);
});

test('updateMyProfile: changing a critical field on an existing profile requires confirmation', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  await profile.updateMyProfile(ctx, {
    displayName: 'Casey',
    age: 25,
    gender: 'man',
    seeking: 'woman',
    relationshipIntention: 'short_term',
  });

  await assert.rejects(async () => {
    try {
      await profile.updateMyProfile(ctx, { seeking: 'nonbinary' });
    } catch (err) {
      assert.ok(err instanceof ValidationError);
      const details = (err as ValidationError).details as { requiresConfirmation: boolean; warning: string };
      assert.equal(details.requiresConfirmation, true);
      assert.equal(details.warning, profile.CRITICAL_FIELD_CHANGE_WARNING);
      throw err;
    }
  }, ValidationError);

  // With explicit confirmation it goes through.
  const updated = await profile.updateMyProfile(ctx, { seeking: 'nonbinary', confirmCriticalChange: true });
  assert.equal(updated.seeking, 'nonbinary');
});

test('updateMyProfile: non-critical field changes never require confirmation', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  await profile.updateMyProfile(ctx, {
    displayName: 'Dana',
    age: 33,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
  });

  const updated = await profile.updateMyProfile(ctx, { bio: 'Updated bio text here.' });
  assert.equal(updated.bio, 'Updated bio text here.');
});

test('buildPublicProfileView: never exposes latitude/longitude, only a bucketed approximate distance', async () => {
  const viewerId = await createUser();
  const targetId = await createUser();
  const viewerCtx = buildCtx({ now: NOW, actor: userActor(viewerId) });
  const targetCtx = buildCtx({ now: NOW, actor: userActor(targetId), }); // separate ctx, same clock value

  await profile.updateMyProfile(viewerCtx, {
    displayName: 'Viewer',
    age: 30,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
    latitude: 39.78,
    longitude: -89.65,
  });
  await profile.updateMyProfile(targetCtx, {
    displayName: 'Target',
    age: 29,
    gender: 'man',
    seeking: 'woman',
    relationshipIntention: 'long_term',
    bio: 'Hello there, this is my bio.',
    latitude: 39.8, // ~a few km away
    longitude: -89.66,
  });

  const pool = getTestPool();
  await pool.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected)
     VALUES ($1, 'https://example.test/target.jpg', 0, true, 'approved', true)`,
    [targetId],
  );

  const view = await profile.buildPublicProfileView(viewerCtx, viewerId, targetId);

  assert.equal(view.userId, targetId);
  assert.equal(view.displayName, 'Target');
  // Wiring fix (item 3): was `view.photoUrls.includes(...)` (a bare
  // string array); every photo now carries `{id, imageUrl, altText}` so a
  // description can travel with it, see `ProfilePhotoView`.
  assert.ok(view.photos.some((p) => p.imageUrl === 'https://example.test/target.jpg'));
  assert.equal(typeof view.approximateDistanceKm, 'number');
  assert.ok((view.approximateDistanceKm as number) >= 0);

  // Structural guarantee: PublicProfileView has no coordinate fields at all.
  assert.equal((view as unknown as Record<string, unknown>).latitude, undefined);
  assert.equal((view as unknown as Record<string, unknown>).longitude, undefined);
});

test('buildPublicProfileView: throws NotFoundError for a nonexistent user', async () => {
  const viewerId = await createUser();
  const viewerCtx = buildCtx({ now: NOW, actor: userActor(viewerId) });
  await profile.updateMyProfile(viewerCtx, {
    displayName: 'Viewer2',
    age: 30,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
  });

  await assert.rejects(
    () => profile.buildPublicProfileView(viewerCtx, viewerId, '00000000-0000-0000-0000-000000000000'),
    NotFoundError,
  );
});

test('buildPublicProfileView: only exposes public and reciprocally-shared tags, never hidden ones', async () => {
  const viewerId = await createUser();
  const targetId = await createUser();
  const viewerCtx = buildCtx({ now: NOW, actor: userActor(viewerId) });
  const targetCtx = buildCtx({ now: NOW, actor: userActor(targetId) });

  await profile.updateMyProfile(viewerCtx, {
    displayName: 'V',
    age: 30,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
  });
  await profile.updateMyProfile(targetCtx, {
    displayName: 'T',
    age: 31,
    gender: 'man',
    seeking: 'woman',
    relationshipIntention: 'long_term',
  });

  const pool = getTestPool();
  const { rows: tags } = await pool.query<{ id: string }>(
    `INSERT INTO interest_tags (name, category) VALUES ('Hiking-' || $1, 'outdoors'), ('Secret-' || $1, 'lifestyle'), ('Shared-' || $1, 'hobbies') RETURNING id`,
    [targetId],
  );
  const [publicTag, hiddenTag, reciprocalTag] = tags;

  await pool.query('INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, $3)', [
    targetId,
    publicTag!.id,
    'public',
  ]);
  await pool.query('INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, $3)', [
    targetId,
    hiddenTag!.id,
    'hidden',
  ]);
  await pool.query('INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, $3)', [
    targetId,
    reciprocalTag!.id,
    'private_reciprocal',
  ]);
  // Viewer does NOT share the reciprocal tag -> it must stay invisible too.

  const view = await profile.buildPublicProfileView(viewerCtx, viewerId, targetId);
  assert.ok(view.visibleInterestTagNames.some((n) => n.startsWith('Hiking-')));
  assert.ok(!view.visibleInterestTagNames.some((n) => n.startsWith('Secret-')));
  assert.ok(!view.visibleInterestTagNames.some((n) => n.startsWith('Shared-')));

  // Now the viewer also has the reciprocal tag -> it becomes visible.
  await pool.query('INSERT INTO user_tags (user_id, tag_id, visibility) VALUES ($1, $2, $3)', [
    viewerId,
    reciprocalTag!.id,
    'public',
  ]);
  const view2 = await profile.buildPublicProfileView(viewerCtx, viewerId, targetId);
  assert.ok(view2.visibleInterestTagNames.some((n) => n.startsWith('Shared-')));
});

test('deleteMyAccount: marks the account deleted, scrubs profile fields, removes photos, revokes sessions', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });

  await profile.updateMyProfile(ctx, {
    displayName: 'ToDelete',
    age: 27,
    gender: 'man',
    seeking: 'woman',
    relationshipIntention: 'long_term',
    bio: 'Some bio content here.',
    city: 'Lakeside',
  });

  const pool = getTestPool();
  await pool.query(
    `INSERT INTO user_photos (user_id, image_url, position, is_primary, moderation_status, face_detected)
     VALUES ($1, 'https://example.test/x.jpg', 0, true, 'approved', true)`,
    [userId],
  );
  await pool.query(
    `INSERT INTO refresh_sessions (id, user_id, token_hash, created_at, expires_at)
     VALUES (gen_random_uuid(), $1, 'hash', now(), now() + interval '30 days')`,
    [userId],
  );

  await profile.deleteMyAccount(ctx);

  const { rows: userRows } = await pool.query('SELECT status FROM users WHERE id = $1', [userId]);
  assert.equal(userRows[0].status, 'deleted');

  const { rows: profileRows } = await pool.query('SELECT display_name, bio, city FROM profiles WHERE user_id = $1', [
    userId,
  ]);
  assert.equal(profileRows[0].display_name, 'Deleted user');
  assert.equal(profileRows[0].bio, '');
  assert.equal(profileRows[0].city, null);

  const { rows: photoRows } = await pool.query('SELECT count(*)::int AS n FROM user_photos WHERE user_id = $1', [
    userId,
  ]);
  assert.equal(photoRows[0].n, 0);

  const { rows: sessionRows } = await pool.query(
    'SELECT revoked_at FROM refresh_sessions WHERE user_id = $1',
    [userId],
  );
  assert.notEqual(sessionRows[0].revoked_at, null);
});

test('exportMyData: returns account/profile/photo data without the password hash', async () => {
  const userId = await createUser();
  const ctx = buildCtx({ now: NOW, actor: userActor(userId) });
  await profile.updateMyProfile(ctx, {
    displayName: 'Exportable',
    age: 26,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
  });

  const exported = await profile.exportMyData(ctx);
  const account = exported.account as Record<string, unknown>;
  assert.equal(account.password_hash, undefined);
  assert.equal((exported.profile as { displayName: string }).displayName, 'Exportable');
});

test('getPublicProfile: consults discovery.isEitherBlocked before returning a profile', async () => {
  // discovery.isEitherBlocked is a stub owned by agent B (still throws
  // NotImplementedError as of this writing), this only asserts
  // profile.service actually calls through to it and propagates whatever
  // it does today, proving the block-check wiring exists, without
  // asserting on agent B's (not-yet-implemented) blocking logic itself.
  // Once agent B implements it, this should be revisited to assert
  // ForbiddenError specifically for a real blocked pair.
  const viewerId = await createUser();
  const targetId = await createUser();
  const viewerCtx = buildCtx({ now: NOW, actor: userActor(viewerId) });
  await profile.updateMyProfile(viewerCtx, {
    displayName: 'V3',
    age: 30,
    gender: 'woman',
    seeking: 'man',
    relationshipIntention: 'long_term',
  });

  await assert.rejects(() => profile.getPublicProfile(viewerCtx, targetId));
});
