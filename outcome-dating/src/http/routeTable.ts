/**
 * src/http/routeTable.ts, the route -> spec-section coverage table
 * (task brief: "Build a route→spec-section table in a comment or doc so
 * coverage is auditable"). Every route registered anywhere under
 * `src/http/routes/*` has exactly one row here; `tests/http/routeTable.test.ts`
 * asserts every §24-listed route from SPEC.md/INTERFACES.md is present, so
 * this table cannot silently drift out of sync with what's actually wired.
 *
 * `role` is the actor type(s) allowed to call the route (see
 * `src/http/auth.ts#requireRole`); `'public'` means no bearer token at all.
 */
export type RouteRole = 'public' | 'user' | 'venue_staff' | 'admin';

export interface RouteTableEntry {
  method: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  path: string;
  spec: string;
  role: RouteRole | RouteRole[];
  /** True for a route not literally named in §24 but added to satisfy a conformance obligation or a §27 admin-panel capability, see the entry's own comment for which. */
  addition?: boolean;
}

export const ROUTE_TABLE: RouteTableEntry[] = [
  // ---- §24.1 Auth ----
  { method: 'POST', path: '/auth/register', spec: '§24.1, §5', role: 'public' },
  { method: 'POST', path: '/auth/login', spec: '§24.1, §5', role: 'public' },
  { method: 'POST', path: '/auth/logout', spec: '§24.1, §28.2', role: 'public' },
  { method: 'POST', path: '/auth/refresh', spec: '§24.1, §28.2', role: 'public' },
  { method: 'POST', path: '/auth/forgot-password', spec: '§24.1', role: 'public' },
  { method: 'POST', path: '/auth/reset-password', spec: '§24.1', role: 'public' },
  { method: 'POST', path: '/auth/verify-email', spec: '§6.2 (auth.service addition)', role: 'public', addition: true },
  { method: 'POST', path: '/auth/resend-verification', spec: '§6.2 (auth.service addition)', role: 'user', addition: true },
  // Optional phone number (build correction, never mandatory; auth.service addition).
  { method: 'POST', path: '/auth/phone', spec: '§5.2/§5.3 (auth.service addition)', role: 'user', addition: true },
  { method: 'POST', path: '/auth/phone/verify', spec: '§5.2/§5.3 (auth.service addition)', role: 'user', addition: true },
  { method: 'DELETE', path: '/auth/phone', spec: '§5.2/§5.3 (auth.service addition)', role: 'user', addition: true },
  { method: 'GET', path: '/auth/phone', spec: '§5.2/§5.3 (auth.service addition)', role: 'user', addition: true },

  // ---- §24.2 Profile ----
  { method: 'GET', path: '/me', spec: '§24.2', role: 'user' },
  { method: 'PATCH', path: '/me', spec: '§24.2', role: 'user' },
  { method: 'DELETE', path: '/me', spec: '§29 (profile.service addition)', role: 'user', addition: true },
  { method: 'GET', path: '/me/data-export', spec: '§29 (profile.service addition)', role: 'user', addition: true },
  { method: 'GET', path: '/me/profile', spec: '§24.2, §7.1', role: 'user' },
  { method: 'PATCH', path: '/me/profile', spec: '§24.2, §7.1, §30.8', role: 'user' },
  { method: 'GET', path: '/me/photos', spec: '§7.2 (addition, photo.service#listMyPhotos was built but unrouted, see docs/ux-api-review.md §3a)', role: 'user', addition: true },
  { method: 'POST', path: '/me/photos', spec: '§24.2, §7.2', role: 'user' },
  { method: 'DELETE', path: '/me/photos/:photoId', spec: '§24.2, §7.2', role: 'user' },
  { method: 'POST', path: '/me/photos/:photoId/primary', spec: '§7.2 (addition)', role: 'user', addition: true },
  { method: 'POST', path: '/me/photos/reorder', spec: '§7.2 (addition)', role: 'user', addition: true },
  { method: 'GET', path: '/me/photo-test-results', spec: '§24.2, §7.3' , role: 'user' },
  { method: 'POST', path: '/me/photo-test-results/:photoId/approve', spec: '§7.3 (addition)', role: 'user', addition: true },
  { method: 'POST', path: '/me/photo-test-results/:photoId/reject', spec: '§7.3 (addition)', role: 'user', addition: true },
  { method: 'GET', path: '/me/behavioral-prompts', spec: '§17 (addition)', role: 'user', addition: true },
  { method: 'POST', path: '/me/behavioral-prompts/:suggestionId/respond', spec: '§17 (addition)', role: 'user', addition: true },

  // ---- §24.3 Questions, the ONE typed question bank (question-system
  // cutover; see question.service.ts's file-level CUTOVER doc). The three
  // paths below are the ones tests/http/routeTable.test.ts hardcodes as
  // required §24.3 routes; every other entry in this block is an addition
  // that exposes a piece of the typed bank the old bank had no equivalent
  // for (paginated bank browsing beyond page 1, next-question selection,
  // tag intensity, avoid-tags). ----
  { method: 'GET', path: '/questions', spec: '§24.3, §8 (typed bank, paginated)', role: 'user' },
  { method: 'GET', path: '/me/answers', spec: '§24.3, §8 (typed bank)', role: 'user' },
  { method: 'PUT', path: '/me/answers', spec: '§24.3, §8 (typed bank: answer, skip, or prefer-not-to-say one question)', role: 'user' },
  { method: 'GET', path: '/questions/next', spec: '§8 next-question selector (addition, src/domain/questions/selector.ts)', role: 'user', addition: true },
  { method: 'GET', path: '/me/tag-intensity', spec: '§8.4 tag intensity (addition, src/domain/questions/tags.ts)', role: 'user', addition: true },
  { method: 'PUT', path: '/me/tag-intensity/:tagId', spec: '§8.4 tag intensity (addition)', role: 'user', addition: true },
  { method: 'GET', path: '/me/avoid-tags', spec: '§8.4 avoid-tags (addition, src/domain/questions/tags.ts)', role: 'user', addition: true },
  { method: 'PUT', path: '/me/avoid-tags', spec: '§8.4 avoid-tags (addition)', role: 'user', addition: true },

  // ---- §24.4 Filters ----
  { method: 'GET', path: '/me/filters', spec: '§24.4, §9', role: 'user' },
  { method: 'PATCH', path: '/me/filters', spec: '§24.4, §9', role: 'user' },
  { method: 'GET', path: '/me/filters/cleanup-preview', spec: 'product-owner correction (addition), count-only preview of the opt-in pending-interest cleanup, see interest.service.ts', role: 'user', addition: true },
  { method: 'POST', path: '/me/filters/cleanup', spec: 'product-owner correction (addition), explicit, user-invoked pending-interest cleanup; never a side effect of a filter update, see interest.service.ts', role: 'user', addition: true },

  // ---- §24.5 Discovery ----
  { method: 'GET', path: '/discovery', spec: '§24.5, §10', role: 'user' },
  { method: 'GET', path: '/discovery/reality', spec: '§9.3 (addition)', role: 'user', addition: true },
  { method: 'GET', path: '/profiles/:userId', spec: '§24.5, §7.1', role: 'user' },
  { method: 'POST', path: '/profiles/:userId/block', spec: '§24.5, §10.2', role: 'user' },
  { method: 'DELETE', path: '/profiles/:userId/block', spec: '§10.2 (addition)', role: 'user', addition: true },
  { method: 'POST', path: '/profiles/:userId/report', spec: '§24.5, §18.3, §30.9', role: 'user' },

  // ---- §24.6 Interests ----
  { method: 'POST', path: '/interests', spec: '§24.6, §11', role: 'user' },
  { method: 'GET', path: '/interests/outgoing', spec: '§24.6, §11', role: 'user' },
  { method: 'GET', path: '/interests/incoming', spec: '§24.6, §11', role: 'user' },
  { method: 'POST', path: '/interests/:interestId/accept', spec: '§24.6, §11.4', role: 'user' },
  { method: 'POST', path: '/interests/:interestId/decline', spec: '§24.6, §11.4', role: 'user' },
  { method: 'POST', path: '/interests/:interestId/cancel', spec: '§24.6, §11.4', role: 'user' },

  // ---- §24.7 Conversations ----
  { method: 'GET', path: '/conversations', spec: '§24.7, §12.1', role: 'user' },
  { method: 'GET', path: '/conversations/:conversationId', spec: '§24.7', role: 'user' },
  { method: 'GET', path: '/conversations/:conversationId/messages', spec: '§24.7, §12.2', role: 'user' },
  { method: 'POST', path: '/conversations/:conversationId/messages', spec: '§24.7, §12.2-5', role: 'user' },
  { method: 'POST', path: '/conversations/:conversationId/archive', spec: '§24.7, §12.7', role: 'user' },
  { method: 'POST', path: '/conversations/:conversationId/read', spec: '§12.2 (addition)', role: 'user', addition: true },
  { method: 'GET', path: '/conversations/:conversationId/timeline', spec: '§12, §13 (product-owner addition, merged message + date-proposal timeline)', role: 'user', addition: true },

  // ---- Matches (product-owner addition, see matches.service.ts) ----
  { method: 'GET', path: '/matches', spec: '§11.4, §24.7 (product-owner addition, "you cannot see your matches")', role: 'user', addition: true },
  { method: 'GET', path: '/matches/:conversationId', spec: '§11.4, §24.7 (product-owner addition)', role: 'user', addition: true },

  // ---- §24.8 Dates ----
  { method: 'GET', path: '/venues', spec: '§24.8, §13.2', role: 'user' },
  { method: 'GET', path: '/venues/:venueId', spec: '§13.2 (addition, venue.service#getVenue was built but unrouted, see docs/ux-api-review.md §10)', role: 'user', addition: true },
  { method: 'GET', path: '/venues/:venueId/time-slots', spec: '§13.2 (addition)', role: 'user', addition: true },
  { method: 'POST', path: '/conversations/:conversationId/date-proposals', spec: '§24.8, §13, §14.2', role: 'user' },
  { method: 'GET', path: '/date-proposals/:dateProposalId', spec: '§24.8', role: 'user' },
  { method: 'POST', path: '/date-proposals/:dateProposalId/accept', spec: '§24.8, §14.2', role: 'user' },
  { method: 'POST', path: '/date-proposals/:dateProposalId/decline', spec: '§24.8', role: 'user' },
  { method: 'POST', path: '/date-proposals/:dateProposalId/cancel', spec: '§24.8, §14.7', role: 'user' },
  { method: 'POST', path: '/date-proposals/:dateProposalId/confirm-attendance', spec: '§24.8, §15.4', role: 'user' },
  { method: 'POST', path: '/date-proposals/:dateProposalId/feedback', spec: '§15.4, §26.2 (addition; legacy compatibility shim over postDateFeedback.service#submitLegacyFeedback, see integrity audit item 1)', role: 'user', addition: true },
  { method: 'POST', path: '/date-proposals/:dateProposalId/check-in', spec: 'post-date check-in (product-owner addition, see postDateFeedback.service.ts)', role: 'user', addition: true },
  { method: 'GET', path: '/date-proposals/:dateProposalId/check-in', spec: 'post-date check-in (product-owner addition, see postDateFeedback.service.ts)', role: 'user', addition: true },

  // ---- §24.9 Tickets ----
  { method: 'GET', path: '/tickets', spec: '§24.9, §15.1', role: 'user' },
  { method: 'GET', path: '/tickets/:ticketId', spec: '§24.9, §15.1', role: 'user' },
  { method: 'POST', path: '/tickets/:ticketId/redeem', spec: '§24.9, §15.3', role: 'user' },
  { method: 'POST', path: '/venue/redeem', spec: '§24.9, §15.3, §4.2', role: 'venue_staff' },
  { method: 'GET', path: '/venue/vouchers', spec: '§4.2 C-4.2.1 (addition)', role: 'venue_staff', addition: true },
  { method: 'GET', path: '/venue/redemptions', spec: '§4.2 (addition)', role: 'venue_staff', addition: true },

  // ---- §24.10 Payments ----
  { method: 'POST', path: '/payment-methods', spec: '§24.10, §14, §28.4', role: 'user' },
  { method: 'GET', path: '/payment-methods', spec: '§24.10', role: 'user' },
  { method: 'DELETE', path: '/payment-methods/:paymentMethodId', spec: '§24.10', role: 'user' },
  { method: 'POST', path: '/webhooks/payments', spec: '§24.10, §25.9', role: 'public' },

  // ---- §24.11 Trust ----
  { method: 'GET', path: '/me/capabilities', spec: '§6.4 (addition, trust.service#can() was built but unrouted, see docs/ux-api-review.md §11)', role: 'user', addition: true },
  { method: 'GET', path: '/me/trust', spec: '§24.11, §6.1, §6.3', role: 'user' },
  { method: 'GET', path: '/me/trust/events', spec: '§24.11, §6.3', role: 'user' },
  { method: 'POST', path: '/me/trust/appeal', spec: '§24.11, §18.6', role: 'user' },

  // ---- §24.12 Reports ----
  { method: 'POST', path: '/reports', spec: '§24.12, §18.3, §30.9', role: 'user' },

  // ---- §24.13 Admin ----
  { method: 'GET', path: '/admin/config', spec: '§24.13, §21, §27', role: 'admin' },
  { method: 'PATCH', path: '/admin/config', spec: '§24.13, §21, §27, §28.6', role: 'admin' },
  { method: 'GET', path: '/admin/questions', spec: '§24.13, §27', role: 'admin' },
  { method: 'POST', path: '/admin/questions', spec: '§24.13, §27, §28.6', role: 'admin' },
  { method: 'PATCH', path: '/admin/questions/:id', spec: '§24.13, §27, §28.6', role: 'admin' },
  { method: 'GET', path: '/admin/venues', spec: '§24.13, §27', role: 'admin' },
  { method: 'POST', path: '/admin/venues', spec: '§24.13, §27, §28.6', role: 'admin' },
  { method: 'PATCH', path: '/admin/venues/:id', spec: '§30.6, §27 (addition, conformance C-30.6.1)', role: 'admin', addition: true },
  { method: 'GET', path: '/admin/users', spec: '§24.13, §27' , role: 'admin' },
  { method: 'GET', path: '/admin/users/:userId', spec: '§27 user-lookup detail (addition)', role: 'admin', addition: true },
  { method: 'GET', path: '/admin/users/:userId/trust-events', spec: '§27 trust event viewer (addition)', role: 'admin', addition: true },
  { method: 'GET', path: '/admin/users/:userId/ledger', spec: '§27 payment ledger viewer (addition)', role: 'admin', addition: true },
  { method: 'GET', path: '/admin/moderation/actions', spec: '§24.13, §27', role: 'admin' },
  { method: 'POST', path: '/admin/feature-flags', spec: '§24.13, §22, §27, §28.6', role: 'admin' },
  { method: 'GET', path: '/admin/feature-flags', spec: '§22, §27 flag manager listing (addition)', role: 'admin', addition: true },
  { method: 'GET', path: '/admin/analytics/overview', spec: '§24.13, §26, §27', role: 'admin' },
  { method: 'POST', path: '/admin/payment-holds/:paymentHoldId/refund', spec: '§4.3.6 dispute override (addition)', role: 'admin', addition: true },
  { method: 'POST', path: '/admin/date-proposals/:dateProposalId/cancel', spec: '§30.6.2 venue-closed refund/cancel path (addition)', role: 'admin', addition: true },
  { method: 'GET', path: '/admin/system-readiness', spec: 'production-guard startup readiness report (addition, operator-only, see src/config/adapters.ts)', role: 'admin', addition: true },

  // ---- Notification centre + device registration (§20.2 in-app channel, C-20.2.1; addition, see docs/ux-api-review.md §13) ----
  { method: 'GET', path: '/notifications', spec: '§20.2 (addition, notification.service#listMyNotifications was built but unrouted)', role: 'user', addition: true },
  { method: 'POST', path: '/notifications/:notificationId/read', spec: '§20.2 (addition, notification.service#markNotificationRead was built but unrouted)', role: 'user', addition: true },
  { method: 'GET', path: '/devices', spec: '§20 (addition, notifications/devices.ts#listMyDeviceTokens was built but unrouted)', role: 'user', addition: true },
  { method: 'POST', path: '/devices', spec: '§20 (addition, notifications/devices.ts#registerDeviceToken was built but unrouted: without this, push notifications cannot work regardless of configuration)', role: 'user', addition: true },
  { method: 'DELETE', path: '/devices', spec: '§20 (addition, notifications/devices.ts#unregisterDeviceToken was built but unrouted)', role: 'user', addition: true },

  // ---- User stats page (product-owner addition, see stats.service.ts) ----
  { method: 'GET', path: '/me/stats', spec: 'product-owner addition, user stats page (see stats.service.ts)', role: 'user', addition: true },
  { method: 'GET', path: '/me/stats/trends', spec: 'product-owner addition, user stats page trend-over-time (see stats.service.ts)', role: 'user', addition: true },
  { method: 'GET', path: '/me/stats/photos', spec: 'product-owner addition, user stats page photo performance (see stats.service.ts)', role: 'user', addition: true },
  { method: 'GET', path: '/me/stats/filters', spec: 'product-owner addition, user stats page filter cost (see stats.service.ts)', role: 'user', addition: true },

  // ---- Admin stats page (product-owner addition, see adminStats.service.ts) ----
  { method: 'GET', path: '/admin/stats/overview', spec: '§26, §27 (addition, richer, rollup-backed admin stats page, see adminStats.service.ts)', role: 'admin', addition: true },
  { method: 'GET', path: '/admin/stats/retention', spec: '§26, §27 (addition, retention-by-cohort, see adminStats.service.ts)', role: 'admin', addition: true },

  // ---- Localization: locale discovery + per-user preference (product-owner addition, see src/domain/i18n/**, i18n.routes.ts) ----
  { method: 'GET', path: '/locales', spec: 'localization addition, supported-locale registry, see src/domain/i18n/locales.ts', role: 'public', addition: true },
  { method: 'GET', path: '/me/locale', spec: 'localization addition, resolves the caller\'s negotiated locale (stored preference over Accept-Language header), see src/domain/i18n/locales.ts#resolveLocale', role: 'user', addition: true },
  { method: 'PUT', path: '/me/locale', spec: 'localization addition, sets the caller\'s stored locale preference, see i18n.routes.ts', role: 'user', addition: true },
];
