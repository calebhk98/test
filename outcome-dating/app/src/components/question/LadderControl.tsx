import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing } from '../../theme/tokens';
import { LADDER_POSITIONS, ladderLabels, type LadderPosition } from '../../domain/ladder';
import type { SingleChoiceDefinition } from '../../api/types';

interface LadderControlProps {
  def: SingleChoiceDefinition;
  position: LadderPosition | null;
  onChange: (position: LadderPosition) => void;
}

/**
 * The single ordered five-position control for a binary preference:
 * deal breaker at one end, "don't care" in the middle, deal breaker at
 * the other. Rendered ONLY when the question's `presentation` field is
 * `'ladder'`, this component never decides that for itself.
 */
export function LadderControl({ def, position, onChange }: LadderControlProps): React.ReactElement {
  const labels = ladderLabels(def);
  return (
    <View accessibilityLabel="Your preference" testID="ladder-control">
      {LADDER_POSITIONS.map((pos) => {
        const selected = position === pos;
        const isDealBreaker = pos === 0 || pos === 4;
        const isMiddle = pos === 2;
        return (
          <Pressable
            key={pos}
            onPress={() => onChange(pos)}
            accessibilityRole="radio"
            accessibilityState={{ checked: selected }}
            accessibilityLabel={labels[pos]}
            testID={`ladder-position-${pos}`}
            style={[
              styles.row,
              selected && styles.rowSelected,
              isDealBreaker && styles.dealBreakerRow,
              isMiddle && styles.middleRow,
            ]}
          >
            <View style={[styles.marker, selected && styles.markerSelected]}>{selected ? <View style={styles.dot} /> : null}</View>
            <Text style={[styles.label, selected && styles.labelSelected, isDealBreaker && styles.dealBreakerLabel]}>
              {labels[pos]}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    borderRadius: radii.md,
    minHeight: 48,
  },
  rowSelected: { backgroundColor: colors.accentMuted },
  dealBreakerRow: {},
  middleRow: {},
  marker: {
    width: 22,
    height: 22,
    borderRadius: radii.pill,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markerSelected: { borderColor: colors.accent },
  dot: { width: 10, height: 10, borderRadius: radii.pill, backgroundColor: colors.accent },
  label: { fontSize: 15, color: colors.textPrimary, flexShrink: 1 },
  labelSelected: { fontWeight: '700', color: colors.accent },
  dealBreakerLabel: { fontWeight: '600' },
});
