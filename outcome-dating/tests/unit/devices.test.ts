import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import {
  registerDeviceToken,
  unregisterDeviceToken,
  listActiveDeviceTokensForUser,
  pruneInvalidToken,
} from '../../src/services/notifications/devices.js';
import { ForbiddenError } from '../../src/lib/errors.js';
import { setupTestDatabase, teardownTestDatabase, buildCtx, userActor, insertUser } from '../../src/services/notifications/testSupport.js';

let pool: pg.Pool;

before(async () => {
  pool = await setupTestDatabase('devices');
});

after(async () => {
  await teardownTestDatabase();
});

test('registerDeviceToken: re-registering the same token does not create a duplicate row', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });

  await registerDeviceToken(ctx, { platform: 'ios', deviceId: 'device-1', pushToken: 'tok-abc' });
  await registerDeviceToken(ctx, { platform: 'ios', deviceId: 'device-1', pushToken: 'tok-abc' });
  await registerDeviceToken(ctx, { platform: 'ios', deviceId: 'device-1', pushToken: 'tok-abc' });

  const { rows } = await pool.query('SELECT * FROM device_tokens WHERE push_token = $1', ['tok-abc']);
  assert.equal(rows.length, 1, 'three registrations of the same token must collapse into one row');

  const tokens = await listActiveDeviceTokensForUser(ctx, user);
  assert.equal(tokens.length, 1);
  assert.equal(tokens[0]!.pushToken, 'tok-abc');
});

test('registerDeviceToken: re-registering updates last_seen_at and stays enabled', async () => {
  const user = await insertUser(pool);
  const clock = undefined; // use default clock progression via successive buildCtx now: values
  void clock;
  const first = buildCtx({ actor: userActor(user), now: new Date('2026-01-01T00:00:00.000Z') });
  await registerDeviceToken(first, { platform: 'android', deviceId: 'device-2', pushToken: 'tok-xyz' });

  const second = buildCtx({ actor: userActor(user), now: new Date('2026-01-02T00:00:00.000Z') });
  const row = await registerDeviceToken(second, { platform: 'android', deviceId: 'device-2', pushToken: 'tok-xyz' });

  assert.equal(row.enabled, true);
  assert.equal(row.lastSeenAt.toISOString(), '2026-01-02T00:00:00.000Z');
});

test('a token moving to a new user (shared/resold device) cuts the previous owner off immediately', async () => {
  const oldOwner = await insertUser(pool);
  const newOwner = await insertUser(pool);
  const oldCtx = buildCtx({ actor: userActor(oldOwner) });
  const newCtx = buildCtx({ actor: userActor(newOwner) });

  await registerDeviceToken(oldCtx, { platform: 'web', deviceId: 'shared-device', pushToken: 'tok-shared' });
  let oldTokens = await listActiveDeviceTokensForUser(oldCtx, oldOwner);
  assert.equal(oldTokens.length, 1, 'old owner should see the token before reassignment');

  // Device is resold / re-logged-in as a different user, same push token.
  await registerDeviceToken(newCtx, { platform: 'web', deviceId: 'shared-device', pushToken: 'tok-shared' });

  oldTokens = await listActiveDeviceTokensForUser(oldCtx, oldOwner);
  assert.equal(oldTokens.length, 0, 'previous owner must no longer be able to see (or be sent to via) the reassigned token');

  const newTokens = await listActiveDeviceTokensForUser(newCtx, newOwner);
  assert.equal(newTokens.length, 1);
  assert.equal(newTokens[0]!.pushToken, 'tok-shared');

  // And there is exactly one physical row, not two — no lingering ghost row under the old owner.
  const { rows } = await pool.query('SELECT user_id FROM device_tokens WHERE push_token = $1', ['tok-shared']);
  assert.equal(rows.length, 1);
  assert.equal(rows[0]!.user_id, newOwner);
});

test('unregisterDeviceToken: disables a token for its own user only', async () => {
  const user = await insertUser(pool);
  const stranger = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await registerDeviceToken(ctx, { platform: 'ios', deviceId: 'd', pushToken: 'tok-logout' });

  const strangerCtx = buildCtx({ actor: userActor(stranger) });
  await unregisterDeviceToken(strangerCtx, 'tok-logout'); // no-op: WHERE user_id = stranger matches nothing
  let tokens = await listActiveDeviceTokensForUser(ctx, user);
  assert.equal(tokens.length, 1, 'a stranger unregistering must not affect the real owner\'s token');

  await unregisterDeviceToken(ctx, 'tok-logout');
  tokens = await listActiveDeviceTokensForUser(ctx, user);
  assert.equal(tokens.length, 0, 'disabled tokens are excluded from the active list by default');
});

test('pruneInvalidToken: deletes the row outright (invalid/unregistered tokens reported by the sender must be pruned automatically)', async () => {
  const user = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await registerDeviceToken(ctx, { platform: 'android', deviceId: 'd2', pushToken: 'tok-dead' });

  await pruneInvalidToken(ctx, 'android', 'tok-dead');

  const { rows } = await pool.query('SELECT * FROM device_tokens WHERE push_token = $1', ['tok-dead']);
  assert.equal(rows.length, 0, 'an invalid token must be deleted, not merely disabled');
});

test('listActiveDeviceTokensForUser: a regular user cannot list another user\'s tokens', async () => {
  const user = await insertUser(pool);
  const stranger = await insertUser(pool);
  const ctx = buildCtx({ actor: userActor(user) });
  await registerDeviceToken(ctx, { platform: 'ios', deviceId: 'd3', pushToken: 'tok-private' });

  const strangerCtx = buildCtx({ actor: userActor(stranger) });
  await assert.rejects(() => listActiveDeviceTokensForUser(strangerCtx, user), ForbiddenError);

  // A system actor (the delivery worker) may read any user's tokens.
  const sysCtx = buildCtx({ actor: { type: 'system', job: 'test' } });
  const tokens = await listActiveDeviceTokensForUser(sysCtx, user);
  assert.equal(tokens.length, 1);
});
