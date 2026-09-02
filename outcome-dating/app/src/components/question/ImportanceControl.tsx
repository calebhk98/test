import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing } from '../../theme/tokens';
import { IMPORTANCE_LABELS, IMPORTANCE_LEVELS } from '../../domain/importance';
import type { ImportanceLevel } from '../../api/types';
import { Caption } from '../Typography';

interface ImportanceControlProps {
  value: ImportanceLevel | null;
  onChange: (value: ImportanceLevel) => void;
}

/** How much this preference matters, the second axis of a `value_importance` answer. Always shown alongside a value control, never alone. */
export function ImportanceControl({ value, onChange }: ImportanceControlProps): React.ReactElement {
  return (
    <View>
      <Caption style={styles.label}>How much does this matter to you?</Caption>
      <View style={styles.row} accessibilityLabel="How much this matters">
        {IMPORTANCE_LEVELS.map((level) => {
          const selected = value === level;
          return (
            <Pressable
              key={level}
              onPress={() => onChange(level)}
              accessibilityRole="radio"
              accessibilityState={{ checked: selected }}
              accessibilityLabel={IMPORTANCE_LABELS[level]}
              style={[styles.chip, selected && styles.chipSelected]}
            >
              <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{IMPORTANCE_LABELS[level]}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  label: { marginBottom: spacing.xs },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  chip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    minHeight: 40,
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  chipSelected: { backgroundColor: colors.accentMuted, borderColor: colors.accent },
  chipText: { fontSize: 13, color: colors.textPrimary, fontWeight: '600' },
  chipTextSelected: { color: colors.accent },
});
