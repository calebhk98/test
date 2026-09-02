import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing } from '../theme/tokens';

export type Tone = 'neutral' | 'positive' | 'caution' | 'critical';

const TONE_STYLES: Record<Tone, { bg: string; fg: string; glyph: string }> = {
  neutral: { bg: colors.surface, fg: colors.textSecondary, glyph: '●' },
  positive: { bg: colors.positiveMuted, fg: colors.positive, glyph: '✓' },
  caution: { bg: colors.cautionMuted, fg: colors.caution, glyph: '▲' },
  critical: { bg: colors.criticalMuted, fg: colors.critical, glyph: '✕' },
};

interface StatusBadgeProps {
  label: string;
  tone: Tone;
}

/**
 * Status is never colour alone: a shape (glyph) and the word itself
 * always ride along with the tint, so a colour-blind reader or a
 * screen reader gets the same information a sighted reader gets from
 * hue.
 */
export function StatusBadge({ label, tone }: StatusBadgeProps): React.ReactElement {
  const t = TONE_STYLES[tone];
  return (
    <View style={[styles.badge, { backgroundColor: t.bg }]} accessible accessibilityLabel={label}>
      <Text style={[styles.glyph, { color: t.fg }]} accessibilityElementsHidden importantForAccessibility="no">
        {t.glyph}
      </Text>
      <Text style={[styles.label, { color: t.fg }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    borderRadius: radii.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    gap: spacing.xs,
  },
  glyph: { fontSize: 12 },
  label: { fontSize: 13, fontWeight: '600' },
});
