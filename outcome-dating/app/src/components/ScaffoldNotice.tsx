import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Body, Caption } from './Typography';
import { colors, radii, spacing } from '../theme/tokens';

interface ScaffoldNoticeProps {
  remaining: string;
}

/**
 * The explicit "this screen is scaffolded, not finished" marker the
 * task brief asks for. Every screen below priority 6 uses this instead
 * of silently looking finished: it fetches and renders real data
 * through the one API client, but the actions, edge-case states, and
 * tests a "properly built" screen would have are not done yet.
 */
export function ScaffoldNotice({ remaining }: ScaffoldNoticeProps): React.ReactElement {
  return (
    <View style={styles.box} accessibilityRole="text" accessibilityLabel={`Not finished: ${remaining}`}>
      <Caption style={styles.label}>SCAFFOLDED, NOT FINISHED</Caption>
      <Body style={styles.text}>{remaining}</Body>
    </View>
  );
}

const styles = StyleSheet.create({
  box: { backgroundColor: colors.cautionMuted, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.lg },
  label: { color: colors.caution, fontWeight: '700', marginBottom: spacing.xs },
  text: { color: colors.textPrimary },
});
