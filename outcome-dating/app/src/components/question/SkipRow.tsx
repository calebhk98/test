import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Button } from '../Button';
import { spacing } from '../../theme/tokens';

interface SkipRowProps {
  onSkip: () => void;
  onPreferNotToSay: () => void;
  disabled?: boolean;
}

/** Both options the task brief requires be reachable without hunting: a plain skip, and a deliberate refusal to answer. Rendered at a fixed, always-visible spot on every question, regardless of type. */
export function SkipRow({ onSkip, onPreferNotToSay, disabled }: SkipRowProps): React.ReactElement {
  return (
    <View style={styles.row}>
      <View style={styles.button}>
        <Button label="Skip" onPress={onSkip} variant="ghost" disabled={disabled} testID="skip-question" />
      </View>
      <View style={styles.button}>
        <Button label="Prefer not to say" onPress={onPreferNotToSay} variant="ghost" disabled={disabled} testID="prefer-not-to-say" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.md },
  button: { flex: 1 },
});
