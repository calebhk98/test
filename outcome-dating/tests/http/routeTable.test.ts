/**
 * Coverage audit: every entry in `src/http/routeTable.ts` is actually
 * registered on the built server, AND every §24-listed route from
 * SPEC.md/INTERFACES.md (i.e. every non-`addition` entry) is present. This
 * is what makes the route -> spec-section table in that file trustworthy
 * rather than aspirational documentation.
 */
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setupTestApp, teardownTestApp } from './testServer.js';
import type { TestApp } from './testServer.js';
import { ROUTE_TABLE } from '../../src/http/routeTable.js';

let t: TestApp;

before(async () => {
  t = await setupTestApp('route_table');
});

after(async () => {
  await teardownTestApp(t);
});

test('every entry in ROUTE_TABLE is actually registered on the server', () => {
  for (const entry of ROUTE_TABLE) {
    const registered = t.app.hasRoute({ method: entry.method, url: entry.path });
    assert.ok(registered, `${entry.method} ${entry.path} (${entry.spec}) is listed in routeTable.ts but not registered`);
  }
});

test('every literal §24 route is present (not just additions)', () => {
  const specRoutes: Array<{ method: string; path: string }> = [
    { method: 'POST', path: '/auth/register' },
    { method: 'POST', path: '/auth/login' },
    { method: 'POST', path: '/auth/logout' },
    { method: 'POST', path: '/auth/refresh' },
    { method: 'POST', path: '/auth/forgot-password' },
    { method: 'POST', path: '/auth/reset-password' },
    { method: 'GET', path: '/me' },
    { method: 'PATCH', path: '/me' },
    { method: 'GET', path: '/me/profile' },
    { method: 'PATCH', path: '/me/profile' },
    { method: 'POST', path: '/me/photos' },
    { method: 'DELETE', path: '/me/photos/:photoId' },
    { method: 'GET', path: '/me/photo-test-results' },
    { method: 'GET', path: '/questions' },
    { method: 'GET', path: '/me/answers' },
    { method: 'PUT', path: '/me/answers' },
    { method: 'GET', path: '/me/filters' },
    { method: 'PATCH', path: '/me/filters' },
    { method: 'GET', path: '/discovery' },
    { method: 'GET', path: '/profiles/:userId' },
    { method: 'POST', path: '/profiles/:userId/block' },
    { method: 'POST', path: '/profiles/:userId/report' },
    { method: 'POST', path: '/interests' },
    { method: 'GET', path: '/interests/outgoing' },
    { method: 'GET', path: '/interests/incoming' },
    { method: 'POST', path: '/interests/:interestId/accept' },
    { method: 'POST', path: '/interests/:interestId/decline' },
    { method: 'POST', path: '/interests/:interestId/cancel' },
    { method: 'GET', path: '/conversations' },
    { method: 'GET', path: '/conversations/:conversationId' },
    { method: 'GET', path: '/conversations/:conversationId/messages' },
    { method: 'POST', path: '/conversations/:conversationId/messages' },
    { method: 'POST', path: '/conversations/:conversationId/archive' },
    { method: 'GET', path: '/venues' },
    { method: 'POST', path: '/conversations/:conversationId/date-proposals' },
    { method: 'GET', path: '/date-proposals/:dateProposalId' },
    { method: 'POST', path: '/date-proposals/:dateProposalId/accept' },
    { method: 'POST', path: '/date-proposals/:dateProposalId/decline' },
    { method: 'POST', path: '/date-proposals/:dateProposalId/cancel' },
    { method: 'POST', path: '/date-proposals/:dateProposalId/confirm-attendance' },
    { method: 'GET', path: '/tickets' },
    { method: 'GET', path: '/tickets/:ticketId' },
    { method: 'POST', path: '/tickets/:ticketId/redeem' },
    { method: 'POST', path: '/venue/redeem' },
    { method: 'POST', path: '/payment-methods' },
    { method: 'GET', path: '/payment-methods' },
    { method: 'DELETE', path: '/payment-methods/:paymentMethodId' },
    { method: 'POST', path: '/webhooks/payments' },
    { method: 'GET', path: '/me/trust' },
    { method: 'GET', path: '/me/trust/events' },
    { method: 'POST', path: '/me/trust/appeal' },
    { method: 'POST', path: '/reports' },
    { method: 'GET', path: '/admin/config' },
    { method: 'PATCH', path: '/admin/config' },
    { method: 'GET', path: '/admin/questions' },
    { method: 'POST', path: '/admin/questions' },
    { method: 'PATCH', path: '/admin/questions/:id' },
    { method: 'GET', path: '/admin/venues' },
    { method: 'POST', path: '/admin/venues' },
    { method: 'GET', path: '/admin/users' },
    { method: 'GET', path: '/admin/moderation/actions' },
    { method: 'POST', path: '/admin/feature-flags' },
    { method: 'GET', path: '/admin/analytics/overview' },
  ];

  for (const r of specRoutes) {
    assert.ok(t.app.hasRoute({ method: r.method as 'GET', url: r.path }), `spec route ${r.method} ${r.path} is not registered`);
  }
});
