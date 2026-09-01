/**
 * src/http/serializers/feedback.ts, `POST`/`GET .../check-in` response
 * shape.
 *
 * This is the explicit allowlist point for the post-date check-in's
 * safety-isolation guarantee (see postDateFeedback.service.ts's module
 * doc, "SAFETY ISOLATION"): every field a check-in response can ever
 * carry is named here, by explicit field access, never a spread, so
 * "does this leak anything to anyone but the submitter" is answerable by
 * reading this one small function.
 *
 * There is only ever ONE view here, not a "self" view and a "other party"
 * view, because there is no code path anywhere (postDateFeedback.service
 * .ts's `submitCheckIn`/`getMyCheckIn` are both hard-scoped to
 * `WHERE user_id = <the calling actor>`) that ever produces the OTHER
 * participant's row for a request to reach this serializer with. Safety
 * isolation here is structural, not a field this function withholds
 * conditionally, there is deliberately no "if this isn't the owner,
 * hide safetyFlag" branch, because the caller can never be anyone but the
 * owner in the first place.
 */
import type { PostDateCheckIn } from '../../services/postDateFeedback.service.js';

export interface PostDateCheckInView {
  id: string;
  dateProposalId: string;
  outcome: PostDateCheckIn['outcome'];
  wouldMeetAgain: PostDateCheckIn['wouldMeetAgain'];
  safetyFlag: PostDateCheckIn['safetyFlag'];
  safetyDetails: PostDateCheckIn['safetyDetails'];
  notes: PostDateCheckIn['notes'];
  reportFiled: boolean;
  createdAt: Date;
}

export function serializeCheckIn(checkIn: PostDateCheckIn): PostDateCheckInView {
  return {
    id: checkIn.id,
    dateProposalId: checkIn.dateProposalId,
    outcome: checkIn.outcome,
    wouldMeetAgain: checkIn.wouldMeetAgain,
    safetyFlag: checkIn.safetyFlag,
    safetyDetails: checkIn.safetyDetails,
    notes: checkIn.notes,
    reportFiled: checkIn.reportFiled,
    createdAt: checkIn.createdAt,
  };
}
