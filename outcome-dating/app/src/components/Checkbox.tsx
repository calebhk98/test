import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing } from '../theme/tokens';

interface CheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  testID?: string;
}

export function Checkbox({ checked, onChange, label, testID }: CheckboxProps): React.ReactElement {
  return (
    <Pressable
      onPress={() => onChange(!checked)}
      style={styles.row}
      accessibilityRole="checkbox"
      accessibilityState={{ checked }}
      accessibilityLabel={label}
      testID={testID}
      hitSlop={8}
    >
      <View style={[styles.box, checked && styles.boxChecked]}>{checked ? <Text style={styles.check}>✓</Text> : null}</View>
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm, paddingVertical: spacing.xs },
  box: {
    width: 24,
    height: 24,
    borderRadius: radii.sm,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  boxChecked: { backgroundColor: colors.accent, borderColor: colors.accent },
  check: { color: colors.textOnAccent, fontSize: 14, fontWeight: '700' },
  label: { flex: 1, fontSize: 16, color: colors.textPrimary, lineHeight: 22 },
});
