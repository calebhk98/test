/**
 * Shared domain types for the whole service layer, mirroring db/migrations/001_init.sql.
 *
 * Every `src/services/*.service.ts` stub imports its row/enum types from
 * here rather than from a sibling service file. That's a deliberate
 * architectural choice: with ~20 service files owned by 5 different
 * parallel agents, importing types peer-to-peer (e.g. `voucher.service.ts`
 * importing `DateProposal` from `dateProposal.service.ts`, which itself
 * needs a `Voucher` type back) creates import cycles as soon as two
 * modules reference each other's row shapes both ways. Centralizing types
 * here means every service file's only "structural" dependency is this
 * one leaf module (plus `src/lib/ctx.ts`); the only inter-service imports
 * left are genuine function calls in one direction (documented per-module
 * in INTERFACES.md), which is real coupling, not an artifact of type
 * plumbing.
 *
 * Field names are camelCase; DB columns are snake_case. Money is always
 * `*Cents: number` (bigint minor units — see INTERFACES.md invariant).
 * Ids are plain `string` (uuid).
 */

// =====================================================================
// Users & trust (§23.1, §6)
// =====================================================================

export type UserStatus = 'active' | 'suspended' | 'deleted';
export type TrustLevel = 'limited' | 'standard' | 'trusted' | 'elite';

export interface User {
  id: string;
  email: string;
  passwordHash: string;
  birthdate: string; // ISO date (YYYY-MM-DD)
  status: UserStatus;
  trustScore: number; // 0-100
  trustLevel: TrustLevel;
  shadowbanned: boolean;
  suspended: boolean;
  emailVerifiedAt: Date | null;
  createdAt: Date;
  lastActiveAt: Date;
}

/** Public-safe user summary — never includes email/passwordHash. */
export interface PublicUserSummary {
  id: string;
  displayName: string;
  trustLevel: TrustLevel;
}

// =====================================================================
// Auth (§24.1, §28.2)
// =====================================================================

export interface AccessTokenPayload {
  sub: string; // userId
  kind: 'access';
  iat: number; // unix seconds
  exp: number; // unix seconds
}

export interface RefreshTokenPayload {
  sub: string; // userId
  kind: 'refresh';
  /** Refresh token family/session id — rotating a refresh token keeps this the same so reuse-after-rotation is detectable. */
  sessionId: string;
  iat: number;
  exp: number;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  accessTokenExpiresAt: Date;
  refreshTokenExpiresAt: Date;
}

// =====================================================================
// Profile (§23.3, §7.1)
// =====================================================================

export interface Profile {
  userId: string;
  displayName: string;
  bio: string;
  city: string | null;
  /** True coordinates. Never sent to other users directly — see `toApproximateDistanceKm`. */
  latitude: number | null;
  longitude: number | null;
  locationFuzzed: boolean;
  age: number;
  gender: string;
  seeking: string;
  relationshipIntention: string;
  profileCompleteness: number; // 0-100
  updatedAt: Date;
}

// =====================================================================
// Photos (§23.4, §23.5, §7.2, §7.3)
// =====================================================================

export type PhotoModerationStatus = 'pending' | 'approved' | 'rejected' | 'flagged';

export interface UserPhoto {
  id: string;
  userId: string;
  imageUrl: string;
  position: number;
  isPrimary: boolean;
  moderationStatus: PhotoModerationStatus;
  faceDetected: boolean | null;
  blurScore: number | null;
  brightnessScore: number | null;
  groupPhotoDetected: boolean | null;
  perceptualHash: string | null;
  createdAt: Date;
}

export interface PhotoExperimentStats {
  id: string;
  userId: string;
  photoId: string;
  impressions: number;
  interestsSent: number;
  interestsAccepted: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface PhotoRecommendation {
  photoId: string;
  currentPosition: number;
  recommendedPosition: number;
  /** e.g. "42% more accepted matches" (spec §7.3 example copy — static template, not generated). */
  acceptedInterestLiftPercent: number;
}

// =====================================================================
// Questions & Answers (§23.6, §23.7, §8)
// =====================================================================

export type QuestionPolarity = 'standard' | 'reversed';

export interface Question {
  id: string;
  slug: string;
  category: string;
  questionText: string;
  selfLeftLabel: string;
  selfRightLabel: string;
  partnerLeftLabel: string;
  partnerRightLabel: string;
  weight: number;
  polarity: QuestionPolarity;
  sensitive: boolean;
  active: boolean;
  createdAt: Date;
  updatedAt: Date;
}

/** 1-5, or null for "prefer not to say" (§8.5). */
export type AnswerValue = 1 | 2 | 3 | 4 | 5 | null;

export interface Answer {
  userId: string;
  questionId: string;
  selfValue: AnswerValue;
  partnerValue: AnswerValue;
  updatedAt: Date;
}

// =====================================================================
// Interest tags (§23.8, §23.9, §8.4)
// =====================================================================

export type TagVisibility = 'public' | 'private_reciprocal' | 'hidden';

export interface InterestTagDef {
  id: string;
  name: string;
  category: string;
  publicDescription: string;
  createdAt: Date;
}

export interface UserTag {
  userId: string;
  tagId: string;
  visibility: TagVisibility;
  createdAt: Date;
}

// =====================================================================
// Filters (§23.10, §9)
// =====================================================================

export type FilterOperator = 'eq' | 'neq' | 'gte' | 'lte' | 'gt' | 'lt' | 'in';

export interface HardFilter {
  userId: string;
  filterKey: string;
  operator: FilterOperator;
  value: unknown; // number | string | array — shape depends on filterKey
  enabled: boolean;
  updatedAt: Date;
}

// =====================================================================
// Discovery (§23.11, §10, §16.3)
// =====================================================================

export interface DiscoveryCandidate {
  userId: string;
  displayName: string;
  age: number;
  approximateDistanceKm: number | null;
  primaryPhotoUrl: string | null;
  /** At most one shared interest tag surfaced per card (§10.1). */
  sharedInterestTag: string | null;
  compatibilityScore: number; // 0-1, sort key
  trustLevel: TrustLevel;
  profileCompleteness: number;
}

export interface DiscoveryEvent {
  id: string;
  viewerUserId: string;
  candidateUserId: string;
  primaryPhotoId: string | null;
  source: string;
  createdAt: Date;
}

/** §9.3 "Reality Dashboard". */
export interface RealityDashboard {
  matchesMyFilters: number; // X
  whoseFiltersIMatch: number; // Y
  mutualMatchPool: number; // Z
}

export interface CompatibilityScoreRow {
  userId: string;
  candidateId: string;
  score: number; // 0-1
  computedAt: Date;
}

// =====================================================================
// Behavioral prompts (§17)
// =====================================================================

export interface BehavioralPromptSuggestion {
  id: string;
  userId: string;
  /** The question this behavior pattern suggests asking — MUST be presented, never auto-answered (§17 rule 1). */
  questionId: string;
  /** e.g. "tag" | "category" — what pattern triggered the suggestion, for the static template copy. */
  triggerKind: string;
  triggerLabel: string;
  createdAt: Date;
}

// =====================================================================
// Interests (§23.12, §11)
// =====================================================================

export type InterestStatus = 'pending' | 'accepted' | 'declined' | 'expired' | 'canceled';

export interface InterestPolicySnapshot {
  'interest.expiry_hours': number;
  'interest.outgoing_pending_limit': number;
  'interest.incoming_pending_limit': number;
}

export interface Interest {
  id: string;
  senderId: string;
  recipientId: string;
  status: InterestStatus;
  policySnapshot: InterestPolicySnapshot;
  createdAt: Date;
  expiresAt: Date;
  acceptedAt: Date | null;
  declinedAt: Date | null;
  canceledAt: Date | null;
  expiredAt: Date | null;
}

// =====================================================================
// Conversations & messages (§23.13, §23.14, §23.15, §12)
// =====================================================================

export type ConversationStatus = 'active' | 'cooling' | 'archived' | 'established';

export interface Conversation {
  id: string;
  userAId: string; // canonically userAId < userBId (see conversations_ordered_pair constraint)
  userBId: string;
  status: ConversationStatus;
  createdAt: Date;
  lastMessageAt: Date | null;
  firstDateCompletedAt: Date | null;
  archivedAt: Date | null;
}

export type MessageFlagType =
  | 'external_contact'
  | 'money_request'
  | 'link'
  | 'crypto'
  | 'spam_pattern'
  | 'abuse_pattern';

export interface MessageFlag {
  id: string;
  messageId: string;
  flagType: MessageFlagType;
  severity: number; // 1-5
  createdAt: Date;
}

export interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  body: string;
  createdAt: Date;
  readAt: Date | null;
  analysisFlags: MessageFlagType[];
}

// =====================================================================
// Text scanning (§12.4, §18.2, §19.3, §19.4)
// =====================================================================

export interface TextScanResult {
  flags: Array<{ type: MessageFlagType; severity: number; matchedPattern: string }>;
  /** Whether a static safety-notice banner should render below the message (§12.5). Never blocks sending by default. */
  showSafetyBanner: boolean;
  /** Static template key for the banner copy, if `showSafetyBanner`. */
  safetyBannerTemplateKey: string | null;
}

// =====================================================================
// Notifications (§20)
// =====================================================================

export type NotificationEventType =
  | 'interest_received'
  | 'interest_accepted'
  | 'interest_declined'
  | 'interest_expiring_soon'
  | 'chat_opened'
  | 'date_proposal_received'
  | 'date_accepted'
  | 'payment_hold_authorized'
  | 'payment_failed'
  | 'ticket_issued'
  | 'date_reminder'
  | 'venue_redeemed'
  | 'post_date_feedback_request'
  | 'chat_cooling'
  | 'trust_level_changed'
  | 'safety_notice'
  // ---- Decision-layer additions (see docs/conformance.md OQ-3): the
  // original registry had no event for these five date-proposal terminal
  // transitions, flagged as a gap by dateProposal.service.ts's module doc.
  | 'date_canceled'
  | 'date_refunded'
  | 'date_disputed'
  | 'date_no_show'
  | 'date_completed';

export type NotificationChannel = 'push' | 'email' | 'in_app';
export type NotificationStatus = 'pending' | 'sent' | 'failed' | 'read';

export interface Notification {
  id: string;
  userId: string;
  eventType: NotificationEventType;
  channel: NotificationChannel;
  /** Key into the static copy template table — NEVER generated text (spec §1, §20). */
  templateKey: string;
  payload: Record<string, unknown>;
  status: NotificationStatus;
  createdAt: Date;
  sentAt: Date | null;
  readAt: Date | null;
}

// =====================================================================
// Venues (§23.16, §13.2)
// =====================================================================

export type VenueCategory =
  | 'coffee'
  | 'dessert'
  | 'drinks'
  | 'walk'
  | 'museum'
  | 'arcade'
  | 'live_music'
  | 'comedy'
  | 'class_activity'
  | 'food_market';

export type RedemptionMethod = 'qr_scan' | 'manual_code';

export interface VenueTimeSlot {
  dayOfWeek: number; // 0-6, Sunday=0
  startMinute: number; // minutes after midnight, local venue time
  endMinute: number;
}

export interface Venue {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  category: VenueCategory;
  active: boolean;
  marginPercent: number;
  timeSlots: VenueTimeSlot[];
  redemptionMethod: RedemptionMethod;
  createdAt: Date;
}

export interface VenueStaffMember {
  id: string;
  userId: string;
  venueId: string;
  active: boolean;
  createdAt: Date;
}

// =====================================================================
// Venue settlements — decision-layer addition (see docs/conformance.md
// OQ-8, db/migrations/007_decisions.sql). §15.4 says an unverified date
// "does not automatically settle venue payment" and §13.2/§23.16 give
// every venue a `margin_percent`, but the original spec defines no payout
// mechanism — this is it.
// =====================================================================

export type VenueSettlementStatus = 'settled' | 'failed';

export interface VenueSettlement {
  id: string;
  venueId: string;
  dateProposalId: string;
  /** Total captured escrow (both participants) this settlement is computed from. */
  grossEscrowCents: number;
  /** The venue's `margin_percent` as it stood at settlement time (independent of later venue edits). */
  marginPercentApplied: number;
  /** `Math.floor(grossEscrowCents * marginPercentApplied / 100)`. */
  venuePayoutCents: number;
  /** `grossEscrowCents - venuePayoutCents` — always exact: `venuePayoutCents + platformCents === grossEscrowCents`. */
  platformCents: number;
  status: VenueSettlementStatus;
  /** Coarse settlement bucket, e.g. `"2026-01"` (UTC year-month at settlement time). */
  settlementPeriod: string;
  createdAt: Date;
  settledAt: Date | null;
  processorReference: string | null;
}

// =====================================================================
// Date proposals (§23.17, §13, §14, §15)
// =====================================================================

export type DateProposalStatus =
  | 'draft'
  | 'pending_acceptance'
  | 'accepted'
  | 'declined'
  | 'expired'
  | 'canceled'
  | 'payment_failed'
  | 'charged'
  | 'ticketed'
  | 'completed'
  | 'completed_unverified' // §15.4 no-scan fallback, both users confirmed
  | 'no_show'
  | 'refunded'
  | 'disputed';

export interface DateProposalPolicySnapshot {
  'date.escrow_amount_cents': number;
  'date.accept_expiry_hours': number;
  'date.full_refund_cutoff_hours': number;
  'date.late_cancel_refund_percent': number;
  'date.no_show_refund_percent': number;
  'date.no_scan_confirmation_hours': number;
  /** Decision-layer addition (OQ-3): hours after a proposal enters `disputed` (itself `scheduledEnd + no_scan_confirmation_hours`) before automated resolution runs. Optional so proposals created before this key existed still parse. */
  'date.dispute_auto_resolve_hours'?: number;
}

export interface DateProposal {
  id: string;
  conversationId: string;
  proposerId: string;
  recipientId: string;
  venueId: string;
  scheduledStart: Date;
  scheduledEnd: Date;
  optionalNote: string | null;
  status: DateProposalStatus;
  policySnapshot: DateProposalPolicySnapshot;
  escrowAmountCents: number;
  createdAt: Date;
  acceptedAt: Date | null;
  declinedAt: Date | null;
  expiredAt: Date | null;
  canceledAt: Date | null;
  chargedAt: Date | null;
  ticketedAt: Date | null;
  completedAt: Date | null;
}

export interface AttendanceConfirmation {
  dateProposalId: string;
  userId: string;
  confirmedAt: Date;
}

export interface PostDateFeedback {
  id: string;
  dateProposalId: string;
  userId: string;
  positive: boolean;
  wouldMeetAgain: boolean | null;
  safetyConcern: boolean;
  notes: string | null;
  createdAt: Date;
}

// =====================================================================
// Payments (§23.18, §23.19, §14, §28.4)
// =====================================================================

export type PaymentHoldStatus =
  | 'pending'
  | 'authorized'
  | 'capture_pending'
  | 'captured'
  | 'released'
  | 'failed'
  | 'refunded';

export interface PaymentHold {
  id: string;
  dateProposalId: string;
  userId: string;
  processor: string; // 'fake' | 'stripe' | ...
  processorIntentId: string | null;
  amountCents: number;
  currency: string;
  status: PaymentHoldStatus;
  authorizedAt: Date | null;
  capturedAt: Date | null;
  releasedAt: Date | null;
  refundedAt: Date | null;
  failureReason: string | null;
}

/**
 * `venue_payout` is a decision-layer addition (see docs/conformance.md
 * OQ-8) — a venue settlement's payout to the venue itself, distinct from
 * the six user-facing types the original spec (§14.8) enumerates.
 */
export type LedgerEntryType = 'authorization' | 'capture' | 'release' | 'refund' | 'dispute' | 'chargeback' | 'venue_payout';

export interface LedgerEntry {
  /**
   * Null only for `type: 'venue_payout'` rows, which pay a venue
   * (`venueId`) rather than a user — every other entry type always carries
   * a non-null `userId` and a null `venueId`, unchanged from the original
   * contract.
   */
  userId: string | null;
  /** Set only for `type: 'venue_payout'` rows (see `userId`). */
  venueId?: string | null;
  id: string;
  dateProposalId: string;
  paymentHoldId: string | null;
  type: LedgerEntryType;
  amountCents: number;
  currency: string;
  processorReference: string | null;
  metadata: Record<string, unknown>;
  createdAt: Date;
}

export interface PaymentMethodSummary {
  id: string;
  userId: string;
  processor: string;
  brand: string | null;
  last4: string | null;
  isDefault: boolean;
  verifiedAt: Date | null;
  createdAt: Date;
}

// =====================================================================
// Vouchers (§23.20, §23.21, §15)
// =====================================================================

export type VoucherStatus = 'issued' | 'redeemed' | 'expired' | 'canceled';

export interface VoucherQrPayload {
  voucher_id: string;
  venue_id: string;
  date_proposal_id: string;
  expires_at: string; // ISO
}

export interface Voucher {
  id: string;
  dateProposalId: string;
  venueId: string;
  code: string;
  qrPayload: string; // signed compact token (see src/lib/signing.ts), decodes to VoucherQrPayload
  status: VoucherStatus;
  issuedAt: Date;
  expiresAt: Date;
  redeemedAt: Date | null;
}

export interface VenueRedemption {
  id: string;
  voucherId: string;
  venueId: string;
  venueStaffId: string | null;
  method: RedemptionMethod;
  createdAt: Date;
}

// =====================================================================
// Trust (§23.24, §6)
// =====================================================================

export interface TrustEvent {
  id: string;
  userId: string;
  eventType: string;
  delta: number;
  metadata: Record<string, unknown>;
  createdAt: Date;
}

/** §6.3 "Users MUST be able to see why their trust level is limited." */
export interface TrustSummary {
  trustLevel: TrustLevel;
  trustScore: number; // may be withheld from the API response depending on product decision; service always returns it
  actionableImprovements: string[]; // static template strings, e.g. "Add a clear face photo"
  recentNegativeEvents: string[]; // static template strings, e.g. "1 missed date"
}

// =====================================================================
// Moderation & reports (§23.22, §23.23, §18)
// =====================================================================

export type ModerationActionType = 'none' | 'warning' | 'restriction' | 'shadowban' | 'suspension';

export interface ModerationAction {
  id: string;
  userId: string;
  action: ModerationActionType;
  reason: string;
  score: number;
  metadata: Record<string, unknown>;
  createdAt: Date;
}

export type ReportCategory =
  | 'fake_profile'
  | 'scam_money_request'
  | 'harassment'
  | 'unsafe_behavior'
  | 'misleading_photos'
  | 'minor_suspected'
  | 'spam'
  | 'no_show'
  | 'inappropriate_content'
  | 'other';

export interface Report {
  id: string;
  reporterId: string;
  reportedId: string;
  conversationId: string | null;
  messageId: string | null;
  category: ReportCategory;
  severity: number;
  details: string | null;
  createdAt: Date;
}

export interface Block {
  id: string;
  blockerId: string;
  blockedId: string;
  createdAt: Date;
}

// =====================================================================
// Appeals (§18.6)
// =====================================================================

export type AppealMethod = 'liveness_check' | 'payment_verification' | 'cooldown' | 'existing_signals';
export type AppealStatus = 'pending' | 'approved' | 'rejected';

export interface Appeal {
  id: string;
  userId: string;
  moderationActionId: string | null;
  method: AppealMethod;
  status: AppealStatus;
  submittedAt: Date;
  resolvedAt: Date | null;
  metadata: Record<string, unknown>;
}

// =====================================================================
// Pagination helper shared by list-returning service functions
// =====================================================================

export interface Page<T> {
  items: T[];
  nextCursor: string | null;
}
