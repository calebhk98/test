/**
 * Wire types for the Outcome Dating API.
 *
 * These are transcribed field-for-field from the server's serializers
 * (src/http/serializers/**) and route handlers (src/http/routes/**) in
 * the backend repository, not invented. Where a route sends a domain
 * object straight through with no serializer (for example date
 * proposals and payment holds), the shape below matches the domain
 * type in src/domain/types.ts with `Date` fields written as the ISO
 * strings they become once JSON-serialized.
 *
 * This file has no runtime code. Every network call in this app goes
 * through `api/client.ts`, which imports these types, so a backend
 * shape change shows up here as a type error instead of a silent
 * runtime mismatch.
 */

// =====================================================================
// Shared
// =====================================================================

export interface Page<T> {
  items: T[];
  nextCursor: string | null;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: unknown;
}

// =====================================================================
// Auth / account (serializers/user.ts, routes/auth.routes.ts)
// =====================================================================

export type UserStatus = 'active' | 'restricted' | 'shadowbanned' | 'suspended' | 'deleted';
export type TrustLevel = 'new' | 'standard' | 'trusted' | 'restricted' | 'high_risk';

export interface MeView {
  id: string;
  email: string;
  status: UserStatus;
  trustLevel: TrustLevel;
  emailVerifiedAt: string | null;
  createdAt: string;
  lastActiveAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  accessTokenExpiresAt: string;
  refreshTokenExpiresAt: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  /** YYYY-MM-DD */
  birthdate: string;
  termsAccepted: boolean;
  city?: string;
  locationPermission?: boolean;
}

export interface LoginInput {
  email: string;
  password: string;
  deviceFingerprint?: string;
}

export interface PhoneStatus {
  hasPhone: boolean;
  verified: boolean;
  countryCode: string | null;
  last2: string | null;
  addedAt: string | null;
  verifiedAt: string | null;
}

// =====================================================================
// Profile (serializers/profile.ts)
// =====================================================================

export type BodyType = 'slim' | 'athletic' | 'average' | 'curvy' | 'muscular' | 'plus_size' | 'prefer_not_to_say';
export type UnitPreference = 'metric' | 'imperial';

export interface MyProfileView {
  userId: string;
  displayName: string;
  bio: string;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
  age: number;
  gender: string;
  seeking: string;
  relationshipIntention: string;
  profileCompleteness: number;
  heightCm: number | null;
  weightG: number | null;
  weightVisible: boolean;
  bodyType: BodyType | null;
  unitPreference: UnitPreference;
  distancePrecisionFloorKm: number | null;
  updatedAt: string;
}

export interface UpdateProfileInput {
  displayName?: string;
  bio?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  age?: number;
  gender?: string;
  seeking?: string;
  relationshipIntention?: string;
  heightCm?: number;
  weightG?: number;
  weightVisible?: boolean;
  bodyType?: BodyType;
  unitPreference?: UnitPreference;
  distancePrecisionFloorKm?: number | null;
  confirmCriticalChange?: boolean;
}

export interface PublicProfileResponse {
  userId: string;
  displayName: string;
  age: number;
  approximateDistanceKm: number | null;
  bio: string;
  photoUrls: string[];
  trustLevel: TrustLevel;
  visibleInterestTagNames: string[];
}

export type PhotoModerationStatus = 'pending' | 'approved' | 'flagged' | 'rejected';

export interface UserPhoto {
  id: string;
  userId: string;
  url: string;
  /** Server-provided alt text. Always render it; never invent one client-side. */
  altText: string | null;
  isPrimary: boolean;
  position: number;
  moderationStatus: PhotoModerationStatus;
  createdAt: string;
}

// =====================================================================
// Questions (serializers/questions.ts, domain/questions/types.ts)
// =====================================================================

export type QuestionType = 'scale' | 'single_choice' | 'multi_choice' | 'frequency';
export type QuestionPresentation = 'ladder' | 'value_importance';
export type ImportanceLevel = 'irrelevant' | 'slight' | 'important' | 'critical' | 'deal_breaker';
export type AnswerStatus = 'unanswered' | 'skipped' | 'prefer_not_to_say' | 'answered';

export interface ChoiceOption {
  key: string;
  label: string;
}

export interface ScaleDefinition {
  type: 'scale';
  min: number;
  max: number;
  minLabel: string;
  maxLabel: string;
  midLabel: string;
}

export interface SingleChoiceDefinition {
  type: 'single_choice';
  options: ChoiceOption[];
}

export interface MultiChoiceDefinition {
  type: 'multi_choice';
  options: ChoiceOption[];
}

export interface FrequencyDefinition {
  type: 'frequency';
  anchors: ChoiceOption[];
}

export type QuestionTypeDefinition = ScaleDefinition | SingleChoiceDefinition | MultiChoiceDefinition | FrequencyDefinition;

export interface QuestionCardView {
  id: string;
  slug: string;
  version: number;
  category: string;
  subcategory: string | null;
  tags: string[];
  questionText: string;
  typeDef: QuestionTypeDefinition;
  presentation: QuestionPresentation;
  sensitive: boolean;
}

export interface QuestionBankPageView {
  items: QuestionCardView[];
  nextCursor: string | null;
}

export interface MyAnswerView {
  questionSlug: string;
  status: AnswerStatus;
  selfValue: unknown | null;
  preferenceValue: unknown | null;
  importance: ImportanceLevel | null;
  answeredAt: string;
  updatedAt: string;
}

/**
 * Body for `PUT /me/answers`. Mirrors
 * `question.service#PutQuestionAnswerInput`: a `skipped` or
 * `prefer_not_to_say` status carries no value; an `answered` status
 * carries either `ladderPosition` (only valid when the question's
 * `presentation` is `'ladder'`) or an explicit `preferenceValue` +
 * `importance` pair, never both.
 */
export type PutQuestionAnswerInput =
  | { slug: string; status: 'skipped' }
  | { slug: string; status: 'prefer_not_to_say' }
  | {
      slug: string;
      status: 'answered';
      selfValue: unknown;
      ladderPosition: 0 | 1 | 2 | 3 | 4;
    }
  | {
      slug: string;
      status: 'answered';
      selfValue: unknown;
      preferenceValue: unknown;
      importance: ImportanceLevel;
    };

// =====================================================================
// Discovery (serializers/discovery.ts)
// =====================================================================

export interface DiscoveryCardView {
  userId: string;
  displayName: string;
  age: number;
  approximateDistanceKm: number | null;
  primaryPhotoUrl: string | null;
  sharedInterestTag: string | null;
  trustLevel: TrustLevel;
}

export interface DiscoveryPage {
  items: DiscoveryCardView[];
  nextCursor: string | null;
  /** Only present when the grid came back empty; exact static server copy, see routes/discovery.routes.ts NO_CANDIDATES_MESSAGE. */
  message?: string;
}

export interface RealityDashboard {
  matchesMyFilters: number;
  whoseFiltersIMatch: number;
  mutualMatchPool: number;
}

// =====================================================================
// Interests (serializers/interests.ts)
// =====================================================================

export type InterestStatus = 'pending' | 'accepted' | 'declined' | 'canceled' | 'expired';

export interface InterestListItemView {
  id: string;
  counterpartUserId: string;
  status: InterestStatus;
  displayName: string;
  primaryPhotoUrl: string | null;
  age: number;
  approximateDistanceKm: number | null;
  createdAt: string;
  expiresAt: string;
  acceptedAt: string | null;
  declinedAt: string | null;
  canceledAt: string | null;
  expiredAt: string | null;
}

export interface InterestListPageView {
  items: InterestListItemView[];
  nextCursor: string | null;
}

// =====================================================================
// Matches / conversations / timeline
// =====================================================================

export type ConversationStatus = 'active' | 'cooling' | 'archived' | 'established';

export interface MatchListItemView {
  conversationId: string;
  matchedUserId: string;
  displayName: string;
  primaryPhotoUrl: string | null;
  approximateDistanceKm: number | null;
  matchedAt: string;
  conversationStatus: ConversationStatus;
  lastMessagePreview: string | null;
  lastMessageAt: string | null;
  unreadCount: number;
  lastActivityAt: string;
}

export interface MatchListPageView {
  items: MatchListItemView[];
  nextCursor: string | null;
}

export interface TimelineMessageEventView {
  kind: 'message';
  id: string;
  occurredAt: string;
  conversationId: string;
  senderId: string;
  body: string;
  readAt: string | null;
}

export type DateProposalEventKind = 'date_proposed' | 'date_accepted' | 'date_declined' | 'date_canceled' | 'date_expired';

export interface TimelineDateProposalEventView {
  kind: DateProposalEventKind;
  id: string;
  occurredAt: string;
  conversationId: string;
  dateProposalId: string;
  proposerId: string;
  recipientId: string;
  venueName: string;
  scheduledStart: string;
  scheduledEnd: string;
  status: DateProposalStatus;
  hasTicket: boolean;
}

export type TimelineEventView = TimelineMessageEventView | TimelineDateProposalEventView;

export interface TimelinePageView {
  items: TimelineEventView[];
  nextCursor: string | null;
}

// =====================================================================
// Venues / date proposals (domain/types.ts, routes/dates.routes.ts)
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

export type RedemptionMethod = 'qr_scan' | 'code_entry';

export interface VenueTimeSlot {
  dayOfWeek: number; // 0-6, Sunday = 0
  startMinute: number;
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
  createdAt: string;
}

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
  | 'completed_unverified'
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
  'date.dispute_auto_resolve_hours'?: number;
}

export interface DateProposal {
  id: string;
  conversationId: string;
  proposerId: string;
  recipientId: string;
  venueId: string;
  scheduledStart: string;
  scheduledEnd: string;
  optionalNote: string | null;
  status: DateProposalStatus;
  policySnapshot: DateProposalPolicySnapshot;
  escrowAmountCents: number;
  createdAt: string;
  acceptedAt: string | null;
  declinedAt: string | null;
  expiredAt: string | null;
  canceledAt: string | null;
  chargedAt: string | null;
  ticketedAt: string | null;
  completedAt: string | null;
}

export interface ProposeDateInput {
  venueId: string;
  scheduledStart: string;
  scheduledEnd: string;
  optionalNote?: string;
}

// ---- Post-date check-in ----

export type CheckInOutcome = 'went_well' | 'went_okay' | 'did_not_go_well' | 'did_not_happen';
export type WouldMeetAgain = 'yes' | 'no' | 'unsure';
export type SafetyFlagLevel = 'none' | 'concern' | 'urgent';

export interface PostDateCheckInView {
  id: string;
  dateProposalId: string;
  outcome: CheckInOutcome;
  wouldMeetAgain: WouldMeetAgain | null;
  safetyFlag: SafetyFlagLevel;
  safetyDetails: string | null;
  notes: string | null;
  reportFiled: boolean;
  createdAt: string;
}

export interface SubmitCheckInInput {
  outcome: CheckInOutcome;
  wouldMeetAgain?: WouldMeetAgain;
  safetyFlag?: SafetyFlagLevel;
  safetyDetails?: string;
  notes?: string;
}

// =====================================================================
// Tickets (serializers/tickets.ts)
// =====================================================================

export type VoucherStatus = 'issued' | 'redeemed' | 'expired' | 'canceled';

export interface MyTicketView {
  id: string;
  dateProposalId: string;
  venueId: string;
  venueName: string;
  venueAddress: string;
  code: string;
  qrPayload: string;
  status: VoucherStatus;
  scheduledStart: string;
  scheduledEnd: string;
  issuedAt: string;
  expiresAt: string;
  redeemedAt: string | null;
}

// =====================================================================
// Payments (serializers/payment.ts)
// =====================================================================

export interface PaymentMethodView {
  id: string;
  processor: string;
  brand: string | null;
  last4: string | null;
  isDefault: boolean;
  verifiedAt: string | null;
  createdAt: string;
}

export interface AddPaymentMethodInput {
  processorToken: string;
  brand?: string;
  last4?: string;
  makeDefault?: boolean;
}

// =====================================================================
// Trust (serializers/trust.ts)
// =====================================================================

export interface TrustSummaryView {
  trustLevel: TrustLevel;
  trustScore?: number;
  actionableImprovements: string[];
  recentNegativeEvents: string[];
}

export type TrustGatedAction = 'browse' | 'send_interest' | 'chat' | 'send_links' | 'propose_date';

export type CapabilityReasonCode =
  | 'payment_method_required'
  | 'reduced_quota_low_trust'
  | 'links_disabled_low_trust'
  | 'links_warning_standard_trust';

export interface CapabilityDecision {
  allowed: boolean;
  /** Present (and true) when allowed but under a reduced quota (low trust). */
  limited?: boolean;
  /** Only meaningful for `send_links`. */
  linkMode?: 'blocked' | 'warn' | 'clickable';
  reasonCode?: CapabilityReasonCode;
}

export type MyCapabilitiesView = Record<TrustGatedAction, CapabilityDecision>;

// =====================================================================
// Filters (services/filter.service.ts)
// =====================================================================

export type FilterOperator = 'eq' | 'neq' | 'gte' | 'lte' | 'gt' | 'lt' | 'in';

export interface UserFilter {
  filterKey: string;
  operator: FilterOperator;
  value: unknown;
  enabled: boolean;
  excludeIfUnset: boolean;
}

export interface UpdateFilterInput {
  filterKey: string;
  operator: FilterOperator;
  value: unknown;
  enabled: boolean;
}

// =====================================================================
// Stats (serializers/stats.ts)
// =====================================================================

export interface SuppressibleCount {
  value: number | null;
  suppressed: boolean;
}

export interface FilterCostEntryView {
  filterKey: string;
  additionalCandidatesIfRemoved: SuppressibleCount;
}

export interface UserFilterCostsView {
  currentPool: SuppressibleCount;
  whoseFiltersIMatch: SuppressibleCount;
  mutualMatchPool: SuppressibleCount;
  perFilter: FilterCostEntryView[];
  candidatesFailingTwoOrMore: SuppressibleCount;
  costliestFilter: FilterCostEntryView | null;
  computedAt: string;
  fromCache: boolean;
}

export interface PoolVennRegionView {
  label: string;
  count: SuppressibleCount;
}

export interface UserPoolVennView {
  setA: PoolVennRegionView;
  setB: PoolVennRegionView;
  intersection: PoolVennRegionView;
  onlyA: PoolVennRegionView;
  onlyB: PoolVennRegionView;
}

export interface UserStatsOverviewView {
  funnel: Record<string, unknown>;
  completeness: Record<string, unknown>;
  responseBehaviour: Record<string, unknown>;
  dateOutcomes: Record<string, unknown>;
  generatedAt: string;
}

// =====================================================================
// Notifications / devices
// =====================================================================

export type NotificationEventType = string;
export type NotificationChannel = 'push' | 'email' | 'in_app';
export type NotificationStatus = 'pending' | 'sent' | 'failed' | 'read';

export interface AppNotification {
  id: string;
  userId: string;
  eventType: NotificationEventType;
  channel: NotificationChannel;
  templateKey: string;
  payload: Record<string, unknown>;
  status: NotificationStatus;
  createdAt: string;
  sentAt: string | null;
  readAt: string | null;
}

export interface RegisterDeviceInput {
  platform: 'ios' | 'android' | 'web';
  deviceId: string;
  pushToken: string;
}

// =====================================================================
// Locales
// =====================================================================

export type LocaleDirection = 'ltr' | 'rtl';

export interface LocaleInfo {
  code: string;
  englishName: string;
  nativeName: string;
  dir: LocaleDirection;
  status: 'shipped' | 'needs_translation';
}
