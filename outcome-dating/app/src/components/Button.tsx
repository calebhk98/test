import React from 'react';
import { ActivityIndicator, GestureResponderEvent, Pressable, StyleSheet, Text } from 'react-native';
import { colors, fontSizes, radii, spacing } from '../theme/tokens';

interface ButtonProps {
  label: string;
  onPress: (event: GestureResponderEvent) => void;
  variant?: 'primary' | 'secondary' | 'destructive' | 'ghost';
  disabled?: boolean;
  loading?: boolean;
  /** Overrides the spoken label when the visible text alone would be ambiguous out of context (e.g. a lone "Accept" on a card in a long list). */
  accessibilityLabel?: string;
  accessibilityHint?: string;
  testID?: string;
}

/** The one button component every screen uses, so focus order, minimum hit target (44pt), and disabled/loading semantics are consistent everywhere rather than re-implemented per screen. */
export function Button({
  label,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  accessibilityLabel,
  accessibilityHint,
  testID,
}: ButtonProps): React.ReactElement {
  const isDisabled = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      testID={testID}
      style={({ pressed }) => [
        styles.base,
        variantStyles[variant],
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' || variant === 'destructive' ? colors.textOnAccent : colors.accent} />
      ) : (
        <Text style={[styles.label, textVariantStyles[variant], isDisabled && styles.disabledLabel]}>{label}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: 48,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  pressed: { opacity: 0.85 },
  disabled: { backgroundColor: colors.disabled, borderColor: colors.disabled },
  label: { fontSize: fontSizes.body, fontWeight: '600' },
  disabledLabel: { color: colors.textOnAccent },
});

const variantStyles = StyleSheet.create({
  primary: { backgroundColor: colors.accent },
  secondary: { backgroundColor: colors.background, borderWidth: 1, borderColor: colors.accent },
  destructive: { backgroundColor: colors.critical },
  ghost: { backgroundColor: 'transparent' },
});

const textVariantStyles = StyleSheet.create({
  primary: { color: colors.textOnAccent },
  secondary: { color: colors.accent },
  destructive: { color: colors.textOnAccent },
  ghost: { color: colors.accent },
});
