import { formatDistance } from '../distance';
import { formatHeight } from '../height';
import { formatWeight } from '../weight';
import { formatCents } from '../money';

describe('formatDistance', () => {
  it('renders metric as whole kilometres', () => {
    expect(formatDistance(12, 'metric')).toBe('12 km');
  });

  it('renders imperial as whole miles', () => {
    expect(formatDistance(16.0934, 'imperial')).toBe('10 mi');
  });

  it('returns null, not a string, when there is no distance to show', () => {
    expect(formatDistance(null, 'metric')).toBeNull();
  });

  it('shows "<1" rather than rounding a nonzero distance down to zero', () => {
    expect(formatDistance(0.4, 'metric')).toBe('<1 km');
  });
});

describe('formatHeight', () => {
  it('renders metric as centimetres', () => {
    expect(formatHeight(180, 'metric')).toBe('180 cm');
  });

  it('renders imperial as feet and inches, not decimal feet', () => {
    expect(formatHeight(180, 'imperial')).toBe("5'11\"");
  });

  it('returns null when unset', () => {
    expect(formatHeight(null, 'metric')).toBeNull();
  });
});

describe('formatWeight', () => {
  it('renders metric as kilograms to one decimal', () => {
    expect(formatWeight(70000, 'metric')).toBe('70.0 kg');
  });

  it('renders imperial as whole pounds', () => {
    expect(formatWeight(70000, 'imperial')).toBe('154 lb');
  });
});

describe('formatCents', () => {
  it('renders whole-dollar amounts with cents', () => {
    expect(formatCents(2000, 'usd', 'en-US')).toBe('$20.00');
  });

  it('renders non-whole amounts correctly', () => {
    expect(formatCents(1999, 'usd', 'en-US')).toBe('$19.99');
  });
});
