/**
 * The one API client module. Every network call in this app goes
 * through an instance of `ApiClient` (the shared singleton exported as
 * `api` at the bottom of this file); no screen or component calls
 * `fetch` directly. Every method is typed against `./types.ts`, which
 * is transcribed from the backend's own serializers, so a server
 * response shape changing surfaces here as a type error rather than a
 * silent runtime bug.
 *
 * Base URL: `Constants.expoConfig.extra.apiBaseUrl` (see app.json),
 * overridable at runtime for a device that can't reach `localhost`
 * (see `setBaseUrl`, used by Settings > Developer in a debug build).
 */
import Constants from 'expo-constants';
import { ApiError, NetworkError } from './errors';
import { clearTokens, loadTokens, saveTokens } from './session';
import type {
  AddPaymentMethodInput,
  ApiErrorBody,
  AppNotification,
  AuthTokens,
  DateProposal,
  DiscoveryPage,
  InterestListPageView,
  LocaleInfo,
  LoginInput,
  MatchListPageView,
  MeView,
  MyAnswerView,
  MyCapabilitiesView,
  MyProfileView,
  MyTicketView,
  Page,
  PaymentMethodView,
  PhoneStatus,
  PostDateCheckInView,
  ProposeDateInput,
  PublicProfileResponse,
  PutQuestionAnswerInput,
  QuestionBankPageView,
  QuestionCardView,
  RealityDashboard,
  RegisterDeviceInput,
  RegisterInput,
  SubmitCheckInInput,
  TimelinePageView,
  TrustSummaryView,
  UpdateFilterInput,
  UpdateProfileInput,
  UserFilter,
  UserFilterCostsView,
  UserPhoto,
  UserPoolVennView,
  UserStatsOverviewView,
  Venue,
  VenueTimeSlot,
} from './types';

function defaultBaseUrl(): string {
  const extra = (Constants.expoConfig?.extra ?? {}) as { apiBaseUrl?: string };
  return extra.apiBaseUrl ?? 'http://localhost:3000';
}

export type UnauthorizedListener = () => void;

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshInFlight: Promise<boolean> | null = null;
  private unauthorizedListeners = new Set<UnauthorizedListener>();

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  onUnauthorized(listener: UnauthorizedListener): () => void {
    this.unauthorizedListeners.add(listener);
    return () => this.unauthorizedListeners.delete(listener);
  }

  /** Called once at app start to restore a session from the keychain. */
  async restoreSession(): Promise<boolean> {
    const tokens = await loadTokens();
    if (!tokens) return false;
    this.accessToken = tokens.accessToken;
    this.refreshToken = tokens.refreshToken;
    return true;
  }

  isAuthenticated(): boolean {
    return this.accessToken !== null;
  }

  private async setSession(tokens: AuthTokens): Promise<void> {
    this.accessToken = tokens.accessToken;
    this.refreshToken = tokens.refreshToken;
    await saveTokens(tokens);
  }

  async signOut(): Promise<void> {
    this.accessToken = null;
    this.refreshToken = null;
    await clearTokens();
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE',
    path: string,
    options: { body?: unknown; auth?: boolean; retry?: boolean } = {},
  ): Promise<T> {
    const { body, auth = true, retry = true } = options;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (auth && this.accessToken) headers.Authorization = `Bearer ${this.accessToken}`;

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch {
      throw new NetworkError();
    }

    if (response.status === 401 && auth && retry && this.refreshToken) {
      const refreshed = await this.tryRefresh();
      if (refreshed) return this.request<T>(method, path, { ...options, retry: false });
      this.unauthorizedListeners.forEach((listener) => listener());
    }

    if (response.status === 204) return undefined as T;

    let json: unknown;
    try {
      json = await response.json();
    } catch {
      json = null;
    }

    if (!response.ok) {
      const body = (json ?? { code: 'unknown', message: 'Unknown error' }) as ApiErrorBody;
      if (response.status === 401 && this.unauthorizedListeners.size > 0) {
        this.unauthorizedListeners.forEach((listener) => listener());
      }
      throw new ApiError(response.status, body);
    }

    return json as T;
  }

  private async tryRefresh(): Promise<boolean> {
    if (!this.refreshToken) return false;
    if (!this.refreshInFlight) {
      this.refreshInFlight = this.doRefresh().finally(() => {
        this.refreshInFlight = null;
      });
    }
    return this.refreshInFlight;
  }

  private async doRefresh(): Promise<boolean> {
    try {
      const result = await this.request<{ tokens: AuthTokens }>('POST', '/auth/refresh', {
        body: { refreshToken: this.refreshToken },
        auth: false,
        retry: false,
      });
      await this.setSession(result.tokens);
      return true;
    } catch {
      await this.signOut();
      return false;
    }
  }

  // ---- Auth (§24.1) ----

  async register(input: RegisterInput): Promise<MeView> {
    const result = await this.request<{ user: MeView; tokens: AuthTokens }>('POST', '/auth/register', {
      body: input,
      auth: false,
    });
    await this.setSession(result.tokens);
    return result.user;
  }

  async login(input: LoginInput): Promise<MeView> {
    const result = await this.request<{ user: MeView; tokens: AuthTokens }>('POST', '/auth/login', {
      body: input,
      auth: false,
    });
    await this.setSession(result.tokens);
    return result.user;
  }

  async logout(): Promise<void> {
    if (this.refreshToken) {
      await this.request<void>('POST', '/auth/logout', { body: { refreshToken: this.refreshToken }, auth: false }).catch(() => {
        /* best effort; the local session is cleared regardless */
      });
    }
    await this.signOut();
  }

  async forgotPassword(email: string): Promise<void> {
    await this.request<void>('POST', '/auth/forgot-password', { body: { email }, auth: false });
  }

  async resendVerification(): Promise<void> {
    await this.request<void>('POST', '/auth/resend-verification', {});
  }

  async getPhoneStatus(): Promise<PhoneStatus> {
    return this.request<PhoneStatus>('GET', '/auth/phone');
  }

  async requestPhoneVerification(phoneNumber: string, country: string): Promise<void> {
    await this.request<void>('POST', '/auth/phone', { body: { phoneNumber, country } });
  }

  async verifyPhone(code: string): Promise<void> {
    await this.request<void>('POST', '/auth/phone/verify', { body: { code } });
  }

  async removePhone(): Promise<void> {
    await this.request<void>('DELETE', '/auth/phone', {});
  }

  // ---- Profile (§24.2) ----

  async getMe(): Promise<MeView> {
    return this.request<MeView>('GET', '/me');
  }

  async getMyProfile(): Promise<MyProfileView> {
    return this.request<MyProfileView>('GET', '/me/profile');
  }

  async updateMyProfile(input: UpdateProfileInput): Promise<MyProfileView> {
    return this.request<MyProfileView>('PATCH', '/me/profile', { body: input });
  }

  async listMyPhotos(): Promise<UserPhoto[]> {
    return this.request<UserPhoto[]>('GET', '/me/photos');
  }

  async uploadPhoto(imageUrl: string): Promise<UserPhoto> {
    return this.request<UserPhoto>('POST', '/me/photos', { body: { imageUrl } });
  }

  async deletePhoto(photoId: string): Promise<void> {
    await this.request<void>('DELETE', `/me/photos/${photoId}`, {});
  }

  async setPrimaryPhoto(photoId: string): Promise<UserPhoto> {
    return this.request<UserPhoto>('POST', `/me/photos/${photoId}/primary`, {});
  }

  // ---- Questions (§24.3) ----

  async listQuestions(params: { category?: string; cursor?: string; limit?: number } = {}): Promise<QuestionBankPageView> {
    return this.request<QuestionBankPageView>('GET', `/questions${toQuery(params)}`);
  }

  async getNextQuestions(count = 1): Promise<{ items: QuestionCardView[] }> {
    return this.request<{ items: QuestionCardView[] }>('GET', `/questions/next${toQuery({ count })}`);
  }

  async getMyAnswers(): Promise<MyAnswerView[]> {
    return this.request<MyAnswerView[]>('GET', '/me/answers');
  }

  async putMyAnswer(input: PutQuestionAnswerInput): Promise<MyAnswerView> {
    return this.request<MyAnswerView>('PUT', '/me/answers', { body: input });
  }

  // ---- Filters (§24.4) ----

  async getMyFilters(): Promise<UserFilter[]> {
    return this.request<UserFilter[]>('GET', '/me/filters');
  }

  async updateMyFilters(filters: UpdateFilterInput[]): Promise<UserFilter[]> {
    return this.request<UserFilter[]>('PATCH', '/me/filters', { body: filters });
  }

  // ---- Discovery (§24.5) ----

  async getDiscoveryGrid(params: { cursor?: string; limit?: number } = {}): Promise<DiscoveryPage> {
    return this.request<DiscoveryPage>('GET', `/discovery${toQuery(params)}`);
  }

  async getRealityDashboard(): Promise<RealityDashboard> {
    return this.request<RealityDashboard>('GET', '/discovery/reality');
  }

  async getPublicProfile(userId: string): Promise<PublicProfileResponse> {
    return this.request<PublicProfileResponse>('GET', `/profiles/${userId}`);
  }

  async blockUser(userId: string): Promise<void> {
    await this.request<unknown>('POST', `/profiles/${userId}/block`, {});
  }

  async reportUser(userId: string, category: string, details?: string): Promise<void> {
    await this.request<unknown>('POST', `/profiles/${userId}/report`, { body: { category, details } });
  }

  // ---- Interests (§24.6) ----

  async sendInterest(recipientId: string): Promise<unknown> {
    return this.request('POST', '/interests', { body: { recipientId } });
  }

  async listOutgoingInterests(params: { cursor?: string; limit?: number } = {}): Promise<InterestListPageView> {
    return this.request<InterestListPageView>('GET', `/interests/outgoing${toQuery(params)}`);
  }

  async listIncomingInterests(params: { cursor?: string; limit?: number } = {}): Promise<InterestListPageView> {
    return this.request<InterestListPageView>('GET', `/interests/incoming${toQuery(params)}`);
  }

  async acceptInterest(interestId: string): Promise<unknown> {
    return this.request('POST', `/interests/${interestId}/accept`, {});
  }

  async declineInterest(interestId: string): Promise<unknown> {
    return this.request('POST', `/interests/${interestId}/decline`, {});
  }

  async cancelInterest(interestId: string): Promise<unknown> {
    return this.request('POST', `/interests/${interestId}/cancel`, {});
  }

  // ---- Matches / conversations (§24.7 + additions) ----

  async listMatches(params: { cursor?: string; limit?: number } = {}): Promise<MatchListPageView> {
    return this.request<MatchListPageView>('GET', `/matches${toQuery(params)}`);
  }

  async getMatch(conversationId: string): Promise<MatchListPageView['items'][number]> {
    return this.request('GET', `/matches/${conversationId}`);
  }

  async getConversationTimeline(conversationId: string, params: { cursor?: string; limit?: number } = {}): Promise<TimelinePageView> {
    return this.request<TimelinePageView>('GET', `/conversations/${conversationId}/timeline${toQuery(params)}`);
  }

  async sendMessage(conversationId: string, body: string): Promise<unknown> {
    return this.request('POST', `/conversations/${conversationId}/messages`, { body: { body } });
  }

  async markConversationRead(conversationId: string, uptoMessageId: string): Promise<void> {
    await this.request<void>('POST', `/conversations/${conversationId}/read`, { body: { uptoMessageId } });
  }

  async archiveConversation(conversationId: string): Promise<unknown> {
    return this.request('POST', `/conversations/${conversationId}/archive`, {});
  }

  // ---- Venues / dates (§24.8) ----

  async listVenues(category?: string): Promise<Venue[]> {
    return this.request<Venue[]>('GET', `/venues${toQuery({ category })}`);
  }

  async getVenue(venueId: string): Promise<Venue> {
    return this.request<Venue>('GET', `/venues/${venueId}`);
  }

  async getVenueTimeSlots(venueId: string, from?: string, to?: string): Promise<VenueTimeSlot[]> {
    return this.request<VenueTimeSlot[]>('GET', `/venues/${venueId}/time-slots${toQuery({ from, to })}`);
  }

  async proposeDate(conversationId: string, input: ProposeDateInput): Promise<DateProposal> {
    return this.request<DateProposal>('POST', `/conversations/${conversationId}/date-proposals`, { body: input });
  }

  async getDateProposal(dateProposalId: string): Promise<DateProposal> {
    return this.request<DateProposal>('GET', `/date-proposals/${dateProposalId}`);
  }

  async acceptDateProposal(dateProposalId: string): Promise<DateProposal> {
    return this.request<DateProposal>('POST', `/date-proposals/${dateProposalId}/accept`, {});
  }

  async declineDateProposal(dateProposalId: string): Promise<DateProposal> {
    return this.request<DateProposal>('POST', `/date-proposals/${dateProposalId}/decline`, {});
  }

  async cancelDateProposal(dateProposalId: string): Promise<DateProposal> {
    return this.request<DateProposal>('POST', `/date-proposals/${dateProposalId}/cancel`, {});
  }

  async confirmAttendance(dateProposalId: string): Promise<DateProposal> {
    return this.request<DateProposal>('POST', `/date-proposals/${dateProposalId}/confirm-attendance`, {});
  }

  async submitCheckIn(dateProposalId: string, input: SubmitCheckInInput): Promise<PostDateCheckInView> {
    return this.request<PostDateCheckInView>('POST', `/date-proposals/${dateProposalId}/check-in`, { body: input });
  }

  async getCheckIn(dateProposalId: string): Promise<PostDateCheckInView> {
    return this.request<PostDateCheckInView>('GET', `/date-proposals/${dateProposalId}/check-in`);
  }

  // ---- Tickets (§24.9) ----

  async listMyTickets(): Promise<MyTicketView[]> {
    return this.request<MyTicketView[]>('GET', '/tickets');
  }

  async getMyTicket(ticketId: string): Promise<MyTicketView> {
    return this.request<MyTicketView>('GET', `/tickets/${ticketId}`);
  }

  // ---- Payments (§24.10) ----

  async listPaymentMethods(): Promise<PaymentMethodView[]> {
    return this.request<PaymentMethodView[]>('GET', '/payment-methods');
  }

  async addPaymentMethod(input: AddPaymentMethodInput): Promise<PaymentMethodView> {
    return this.request<PaymentMethodView>('POST', '/payment-methods', { body: input });
  }

  async deletePaymentMethod(paymentMethodId: string): Promise<void> {
    await this.request<void>('DELETE', `/payment-methods/${paymentMethodId}`, {});
  }

  // ---- Trust (§24.11) ----

  async getMyTrust(): Promise<TrustSummaryView> {
    return this.request<TrustSummaryView>('GET', '/me/trust');
  }

  async listMyTrustEvents(params: { cursor?: string; limit?: number } = {}): Promise<Page<unknown>> {
    return this.request('GET', `/me/trust/events${toQuery(params)}`);
  }

  async getMyCapabilities(): Promise<MyCapabilitiesView> {
    return this.request<MyCapabilitiesView>('GET', '/me/capabilities');
  }

  // ---- Stats ----

  async getMyStatsOverview(): Promise<UserStatsOverviewView> {
    return this.request<UserStatsOverviewView>('GET', '/me/stats');
  }

  async getMyFilterCosts(refresh = false): Promise<UserFilterCostsView> {
    return this.request<UserFilterCostsView>('GET', `/me/stats/filters${toQuery({ refresh })}`);
  }

  async getMyPoolVenn(): Promise<UserPoolVennView> {
    return this.request<UserPoolVennView>('GET', '/me/stats/venn');
  }

  // ---- Notifications / devices ----

  async listNotifications(params: { cursor?: string; limit?: number; unreadOnly?: boolean } = {}): Promise<Page<AppNotification>> {
    return this.request<Page<AppNotification>>('GET', `/notifications${toQuery(params)}`);
  }

  async markNotificationRead(notificationId: string): Promise<void> {
    await this.request<void>('POST', `/notifications/${notificationId}/read`, {});
  }

  async registerDevice(input: RegisterDeviceInput): Promise<unknown> {
    return this.request('POST', '/devices', { body: input });
  }

  // ---- Locales ----

  async listLocales(): Promise<LocaleInfo[]> {
    return this.request<LocaleInfo[]>('GET', '/locales', { auth: false });
  }

  async setMyLocale(locale: string): Promise<void> {
    await this.request<void>('PUT', '/me/locale', { body: { locale } });
  }
}

function toQuery(params: Record<string, string | number | boolean | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined);
  if (entries.length === 0) return '';
  const search = new URLSearchParams();
  for (const [key, value] of entries) search.set(key, String(value));
  return `?${search.toString()}`;
}

export const api = new ApiClient(defaultBaseUrl());
export { ApiClient };
