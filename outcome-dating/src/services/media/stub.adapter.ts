import { createHash } from 'node:crypto';
import type { ImageModerationPort, PhotoAnalysisInput, PhotoAnalysisResult } from './moderation.port.js';

/**
 * No-ML stand-in for `ImageModerationPort` (spec §7.2 "no human moderation
 * assumed" combined with the MVP constraint of no generative/ML models).
 * Behavior is a pure, deterministic function of `imageUrl`, same URL
 * always analyzes the same way, so seed data and tests are reproducible
 * without a real vision model:
 *
 *   - `imageUrl` contains "noface"   -> faceDetected = false
 *   - `imageUrl` contains "nsfw"     -> nudityDetected = true (=> rejected)
 *   - `imageUrl` contains "weapon"   -> weaponsDetected = true (=> rejected)
 *   - `imageUrl` contains "illegal"  -> illegalContentDetected = true (=> rejected)
 *   - `imageUrl` contains "blurry"   -> blurScore = 0.9 (=> flagged)
 *   - `imageUrl` contains "group"    -> groupPhotoDetected = true
 *   - `imageUrl` contains "dup:<n>"  -> perceptualHash is the literal value
 *     `n`, so seed/test data can force two photos to collide for duplicate-
 *     detection testing; otherwise the hash is sha256(imageUrl).
 *   - anything else -> a plausible clean photo (approved).
 *
 * A real adapter (AWS Rekognition, Vision API, self-hosted model) drops in
 * behind the same `ImageModerationPort` interface with zero call-site
 * changes.
 */
export class StubMediaModerationAdapter implements ImageModerationPort {
  readonly name = 'stub';

  async analyzePhoto(input: PhotoAnalysisInput): Promise<PhotoAnalysisResult> {
    const url = input.imageUrl.toLowerCase();

    const faceDetected = !url.includes('noface');
    const nudityDetected = url.includes('nsfw');
    const weaponsDetected = url.includes('weapon');
    const illegalContentDetected = url.includes('illegal');
    const groupPhotoDetected = url.includes('group');
    const blurScore = url.includes('blurry') ? 0.9 : 0.1;
    const brightnessScore = url.includes('dark') ? 0.1 : 0.6;

    const dupMatch = /dup:([a-z0-9_-]+)/.exec(url);
    const perceptualHash = dupMatch ? `dup_${dupMatch[1]}` : createHash('sha256').update(url).digest('hex');

    const rejectionReasons: string[] = [];
    if (nudityDetected) rejectionReasons.push('nudity_detected');
    if (weaponsDetected) rejectionReasons.push('weapons_detected');
    if (illegalContentDetected) rejectionReasons.push('illegal_content_detected');
    if (input.isCandidatePrimary && !faceDetected) rejectionReasons.push('primary_photo_missing_face');

    let moderationStatus: PhotoAnalysisResult['moderationStatus'];
    if (rejectionReasons.length > 0) {
      moderationStatus = 'rejected';
    } else if (blurScore > 0.7 || groupPhotoDetected) {
      moderationStatus = 'flagged';
    } else {
      moderationStatus = 'approved';
    }

    return {
      faceDetected,
      blurScore,
      brightnessScore,
      groupPhotoDetected,
      nudityDetected,
      weaponsDetected,
      illegalContentDetected,
      perceptualHash,
      moderationStatus,
      rejectionReasons,
    };
  }
}
