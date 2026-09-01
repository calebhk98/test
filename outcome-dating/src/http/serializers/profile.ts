/**
 * src/http/serializers/profile.ts — profile views.
 *
 * `serializeMyProfile` is the ONLY place exact `latitude`/`longitude` may
 * reach an HTTP response — the owner editing their own profile needs it
 * (e.g. to re-render a map pin), and `Profile` (from `profile.service.ts`)
 * is only ever handed to the caller for their OWN profile
 * (`profile.getMyProfile`). `serializePublicProfile` passes through
 * `profile.service#getPublicProfile`'s `PublicProfileView`, which
 * structurally has no coordinate fields at all (see that service's own
 * doc comment) — this serializer is an explicit allowlist on top of that
 * structural guarantee, not a substitute for it (spec §7.1/§28.5, C-28.5.1).
 */
import type { PublicProfileView, ProfileWithAttributes } from '../../services/profile.service.js';
import type { BodyType } from '../../domain/units/bodyType.js';
import type { UnitPreference } from '../../domain/units/preference.js';

/**
 * `ProfileWithAttributes` (`profile.service.ts`) has always carried
 * `heightCm`/`weightG`/`weightVisible`/`bodyType`/`unitPreference`/
 * `distancePrecisionFloorKm` — `getMyProfile`/`updateMyProfile` compute
 * and persist all six. This serializer previously forwarded only the
 * base `Profile` fields, so a value the owner just saved via
 * `PATCH /me/profile` never came back on the next `GET /me/profile` — a
 * broken save-then-reload round trip on the Settings screen (see
 * docs/ux-api-review.md §3b). All six are included below now.
 * `distancePrecisionFloorKm: null` is the "unset" toggle — it means "use
 * the platform default distance-fuzzing bucket," not "no value"; the
 * client should render it as a switch/checkbox on top of whatever numeric
 * floor the owner might otherwise pick, exactly mirroring
 * `UpdateProfileInput.distancePrecisionFloorKm`'s own null-means-default
 * contract so a client can round-trip "leave this unset" without having
 * to invent a sentinel value of its own.
 */
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
  /** `null` = unset, use the platform default bucket (see this interface's doc). */
  distancePrecisionFloorKm: number | null;
  updatedAt: string;
}

export function serializeMyProfile(profile: ProfileWithAttributes): MyProfileView {
  return {
    userId: profile.userId,
    displayName: profile.displayName,
    bio: profile.bio,
    city: profile.city,
    latitude: profile.latitude,
    longitude: profile.longitude,
    age: profile.age,
    gender: profile.gender,
    seeking: profile.seeking,
    relationshipIntention: profile.relationshipIntention,
    profileCompleteness: profile.profileCompleteness,
    heightCm: profile.heightCm,
    weightG: profile.weightG,
    weightVisible: profile.weightVisible,
    bodyType: profile.bodyType,
    unitPreference: profile.unitPreference,
    distancePrecisionFloorKm: profile.distancePrecisionFloorKm,
    updatedAt: profile.updatedAt.toISOString(),
  };
}

export interface PublicProfileResponse {
  userId: string;
  displayName: string;
  age: number;
  approximateDistanceKm: number | null;
  bio: string;
  photoUrls: string[];
  trustLevel: PublicProfileView['trustLevel'];
  visibleInterestTagNames: string[];
}

/** Explicit allowlist over `PublicProfileView` — never spreads the object, so an accidental future field addition to that type (e.g. a raw coordinate) does not automatically reach the wire. */
export function serializePublicProfile(view: PublicProfileView): PublicProfileResponse {
  return {
    userId: view.userId,
    displayName: view.displayName,
    age: view.age,
    approximateDistanceKm: view.approximateDistanceKm,
    bio: view.bio,
    photoUrls: view.photoUrls,
    trustLevel: view.trustLevel,
    visibleInterestTagNames: view.visibleInterestTagNames,
  };
}
