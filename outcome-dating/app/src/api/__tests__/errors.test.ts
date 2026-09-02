import { ApiError, NetworkError, messageForError, isOffline } from '../errors';

describe('messageForError', () => {
  it('maps a known code to its written sentence, not the raw server message', () => {
    const error = new ApiError(409, { code: 'conflict', message: "Illegal date proposal transition: 'accepted' -> 'refunded'" });
    const text = messageForError(error);
    expect(text).not.toContain('Illegal date proposal transition');
    expect(text).not.toContain("'accepted' -> 'refunded'");
  });

  it('gives the daily-interest-limit conflict a specific, friendlier sentence', () => {
    const error = new ApiError(429, { code: 'rate_limited', message: 'limit reached', details: { limit: 5, kind: 'daily_outgoing' } });
    expect(messageForError(error)).toMatch(/sent as many interests/i);
  });

  it('falls back to one calm generic sentence for an unrecognised code', () => {
    const error = new ApiError(500, { code: 'something_new_the_client_has_never_seen', message: 'internal diagnostic string' });
    const text = messageForError(error);
    expect(text).not.toContain('internal diagnostic string');
    expect(text.length).toBeGreaterThan(0);
  });

  it('gives a distinct, honest message for being offline', () => {
    expect(messageForError(new NetworkError())).toMatch(/offline/i);
    expect(isOffline(new NetworkError())).toBe(true);
  });

  it('does not treat a server ApiError as offline', () => {
    expect(isOffline(new ApiError(400, { code: 'validation_error', message: 'bad' }))).toBe(false);
  });
});
