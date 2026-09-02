import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing } from '../../theme/tokens';
import type { ChoiceOption } from '../../api/types';

interface ChoiceGroupProps {
  options: ChoiceOption[];
  value: string | null;
  onChange: (key: string) => void;
  accessibilityLabel: string;
}

/** Single-select chip row, radio semantics. Used for a self-value pick (one option describes you). */
export function ChoiceGroup({ options, value, onChange, accessibilityLabel }: ChoiceGroupProps): React.ReactElement {
  return (
    <View style={styles.row} accessibilityLabel={accessibilityLabel}>
      {options.map((option) => {
        const selected = value === option.key;
        return (
          <Pressable
            key={option.key}
            onPress={() => onChange(option.key)}
            accessibilityRole="radio"
            accessibilityState={{ checked: selected }}
            accessibilityLabel={option.label}
            style={[styles.chip, selected && styles.chipSelected]}
          >
            <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

interface MultiChoiceGroupProps {
  options: ChoiceOption[];
  value: string[];
  onChange: (keys: string[]) => void;
  accessibilityLabel: string;
}

/** Multi-select chip row, checkbox semantics. Used for a preference set (which options would be acceptable) and for multi_choice self-values. */
export function MultiChoiceGroup({ options, value, onChange, accessibilityLabel }: MultiChoiceGroupProps): React.ReactElement {
  function toggle(key: string): void {
    onChange(value.includes(key) ? value.filter((k) => k !== key) : [...value, key]);
  }

  return (
    <View style={styles.row} accessibilityLabel={accessibilityLabel}>
      {options.map((option) => {
        const selected = value.includes(option.key);
        return (
          <Pressable
            key={option.key}
            onPress={() => toggle(option.key)}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: selected }}
            accessibilityLabel={option.label}
            style={[styles.chip, selected && styles.chipSelected]}
          >
            <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 44,
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  chipSelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  chipText: { fontSize: 15, color: colors.textPrimary, fontWeight: '600' },
  chipTextSelected: { color: colors.textOnAccent },
});
