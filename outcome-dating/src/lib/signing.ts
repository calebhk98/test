import { createHmac, timingSafeEqual } from 'node:crypto';

/**
 * A small HMAC-SHA256 "compact token" format shared by:
 *  - auth access/refresh tokens (spec §24.1, §28.2), and
 *  - the voucher QR payload (spec §15.2 — "signed JWT or similar signed token").
 *
 * We deliberately do NOT pull in a JWT library: the spec only requires a
 * *signed* token, and a minimal `base64url(json).base64url(hmac)` format
 * avoids JWT footguns (alg=none, header confusion) while staying trivially
 * inspectable. Format:
 *
 *   base64url(JSON.stringify(payload)) + "." + base64url(hmac-sha256(secret, payloadPart))
 *
 * `sign` and `verify` are generic over the payload shape; callers (auth
 * service, voucher service) define their own payload interfaces.
 */

export interface SignedToken<T> {
  payload: T;
  compact: string;
}

function b64urlEncode(input: Buffer | string): string {
  return Buffer.from(input).toString('base64url');
}

function b64urlDecode(input: string): Buffer {
  return Buffer.from(input, 'base64url');
}

export function sign<T>(payload: T, secret: string): SignedToken<T> {
  const payloadPart = b64urlEncode(JSON.stringify(payload));
  const sig = createHmac('sha256', secret).update(payloadPart).digest();
  const compact = `${payloadPart}.${b64urlEncode(sig)}`;
  return { payload, compact };
}

export class InvalidSignatureError extends Error {
  constructor() {
    super('Invalid or malformed signed token');
    this.name = 'InvalidSignatureError';
  }
}

/**
 * Verify and decode a compact token produced by `sign`. Throws
 * `InvalidSignatureError` on any structural or signature mismatch — callers
 * should catch and translate to `UnauthorizedError` (auth tokens) or a
 * voucher-specific rejection, as appropriate for their context.
 */
export function verify<T>(compact: string, secret: string): T {
  const parts = compact.split('.');
  if (parts.length !== 2) throw new InvalidSignatureError();
  const [payloadPart, sigPart] = parts as [string, string];

  const expectedSig = createHmac('sha256', secret).update(payloadPart).digest();
  let providedSig: Buffer;
  try {
    providedSig = b64urlDecode(sigPart);
  } catch {
    throw new InvalidSignatureError();
  }
  if (providedSig.length !== expectedSig.length || !timingSafeEqual(providedSig, expectedSig)) {
    throw new InvalidSignatureError();
  }

  try {
    return JSON.parse(b64urlDecode(payloadPart).toString('utf8')) as T;
  } catch {
    throw new InvalidSignatureError();
  }
}
