/**
 * Design tokens. A small, deliberately boring palette: text colour
 * alone is never how status is conveyed (every status pairs a token
 * colour with an icon or word, see components/StatusBadge.tsx), and
 * every size below is a minimum, not a fixed box, so the layout
 * survives a person's large-text accessibility setting instead of
 * clipping it.
 */
export const colors = {
  background: '#FFFFFF',
  surface: '#F7F5F3',
  border: '#E4E0DB',
  textPrimary: '#1C1B1A',
  textSecondary: '#5B5854',
  textOnAccent: '#FFFFFF',
  accent: '#B3402A',
  accentMuted: '#F1DAD3',
  positive: '#2E6B4F',
  positiveMuted: '#DCEEE4',
  caution: '#8A5A00',
  cautionMuted: '#F7E7C8',
  critical: '#A3231A',
  criticalMuted: '#F6DAD7',
  disabled: '#C9C4BD',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radii = {
  sm: 8,
  md: 12,
  lg: 20,
  pill: 999,
} as const;

export const fontSizes = {
  caption: 13,
  body: 16,
  bodyLarge: 18,
  title: 22,
  headline: 28,
} as const;
