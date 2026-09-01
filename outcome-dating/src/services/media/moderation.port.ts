import type { PhotoModerationStatus } from '../../domain/types.js';

/**
 * ImageModerationPort, the port `photo.service.ts` calls to analyze an
 * uploaded photo. Spec §7.2 requires, with "no human moderation assumed":
 *
 *   1. face detection on the first/primary photo,
 *   2. automatic blocking of nudity, weapons, and known illegal imagery,
 *   3. perceptual-hash based duplicate/scam-image flagging (§18.2).
 *
 * This is a pure, stateless "image in, structured signals out" adapter,
 * it does NOT query the database. Cross-user duplicate detection (matching
 * one photo's `perceptualHash` against every other user's stored hashes)
 * is `photo.service.ts`'s job, using the DB `user_photos.perceptual_hash`
 * index; this port only produces the hash for one image.
 *
 * MVP ships `StubMediaModerationAdapter` (deterministic, no ML). A real
 * adapter (AWS Rekognition, Google Vision, a hosted moderation API, or a
 * self-hosted model) implements the same interface, nothing else in the
 * codebase should need to change.
 */

export interface PhotoAnalysisInput {
  imageUrl: string;
  /** True when analyzing the photo currently in the user's primary/first slot, face detection is a hard gate only for this one (spec §7.2 rule 2). */
  isCandidatePrimary: boolean;
}

export interface PhotoAnalysisResult {
  faceDetected: boolean;
  /** 0 (sharp), 1 (very blurry). */
  blurScore: number;
  /** 0 (very dark), 1 (very bright). */
  brightnessScore: number;
  groupPhotoDetected: boolean;
  nudityDetected: boolean;
  weaponsDetected: boolean;
  illegalContentDetected: boolean;
  /** Perceptual hash (e.g. pHash/aHash hex string) for duplicate/scam-image matching (§7.2, §18.2). */
  perceptualHash: string;
  /**
   * Overall verdict, already combining the raw signals with policy
   * (nudity/weapons/illegal => 'rejected'; missing required face on a
   * primary-candidate photo => 'rejected'; borderline signals =>
   * 'flagged'; otherwise 'approved'). `photo.service.ts` persists this
   * directly to `user_photos.moderation_status`, it should not need to
   * re-derive policy from the raw booleans, though they're returned too
   * for auditability (`user_photos` stores face/blur/brightness/group
   * columns individually).
   */
  moderationStatus: PhotoModerationStatus;
  rejectionReasons: string[];
}

export interface ImageModerationPort {
  readonly name: string;
  analyzePhoto(input: PhotoAnalysisInput): Promise<PhotoAnalysisResult>;
}
