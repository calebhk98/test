import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radii, spacing } from '../../theme/tokens';
import { Caption } from '../Typography';
import type { ScaleDefinition } from '../../api/types';

interface ScaleControlProps {
  def: ScaleDefinition;
  value: number | null;
  onChange: (value: number) => void;
  accessibilityLabel: string;
}

/** An ordered Likert scale with a labelled midpoint, never a bare 1-5 with an unlabelled middle (the exact bug user testing flagged, see the product review). */
export function ScaleControl({ def, value, onChange, accessibilityLabel }: ScaleControlProps): React.ReactElement {
  const values = rangeInclusive(def.min, def.max);
  const midpoint = (def.min + def.max) / 2;

  function labelFor(n: number): string | null {
    if (n === def.min) return def.minLabel;
    if (n === def.max) return def.maxLabel;
    if (n === midpoint) return def.midLabel;
    return null;
  }

  return (
    <View accessibilityLabel={accessibilityLabel}>
      <View style={styles.row}>
        {values.map((n) => {
          const selected = value === n;
          return (
            <Pressable
              key={n}
              onPress={() => onChange(n)}
              accessibilityRole="radio"
              accessibilityState={{ checked: selected }}
              accessibilityLabel={labelFor(n) ?? String(n)}
              style={[styles.cell, selected && styles.cellSelected]}
            >
              <Text style={[styles.cellText, selected && styles.cellTextSelected]}>{n}</Text>
            </Pressable>
          );
        })}
      </View>
      <View style={styles.labelsRow}>
        <Caption style={styles.edgeLabel}>{def.minLabel}</Caption>
        <Caption style={styles.midLabel}>{def.midLabel}</Caption>
        <Caption style={[styles.edgeLabel, styles.rightAlign]}>{def.maxLabel}</Caption>
      </View>
    </View>
  );
}

function rangeInclusive(min: number, max: number): number[] {
  const out: number[] = [];
  for (let i = min; i <= max; i++) out.push(i);
  return out;
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.xs, justifyContent: 'space-between' },
  cell: {
    flex: 1,
    minHeight: 44,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.sm,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  cellSelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  cellText: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  cellTextSelected: { color: colors.textOnAccent },
  labelsRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.xs },
  edgeLabel: { flex: 1 },
  midLabel: { flex: 1, textAlign: 'center' },
  rightAlign: { textAlign: 'right' },
});
