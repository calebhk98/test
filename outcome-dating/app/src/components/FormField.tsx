import React, { useId } from 'react';
import { StyleSheet, Text, TextInput, TextInputProps, View } from 'react-native';
import { colors, fontSizes, radii, spacing } from '../theme/tokens';

interface FormFieldProps extends TextInputProps {
  label: string;
  error?: string | null;
  hint?: string;
}

/** A labeled text input with its label, hint, and error all wired into one `accessibilityLabel`/`accessibilityHint` so a screen reader announces the same thing a sighted person reads. */
export function FormField({ label, error, hint, style, ...inputProps }: FormFieldProps): React.ReactElement {
  const id = useId();
  const describedBits = [hint, error].filter(Boolean).join('. ');
  return (
    <View style={styles.container}>
      <Text nativeID={`${id}-label`} style={styles.label}>
        {label}
      </Text>
      <TextInput
        {...inputProps}
        accessibilityLabel={label}
        accessibilityHint={describedBits || undefined}
        accessibilityLabelledBy={`${id}-label`}
        placeholderTextColor={colors.textSecondary}
        style={[styles.input, error ? styles.inputError : null, style]}
      />
      {hint && !error ? <Text style={styles.hint}>{hint}</Text> : null}
      {error ? (
        <Text style={styles.error} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: spacing.md },
  label: { fontSize: fontSizes.body, fontWeight: '600', color: colors.textPrimary, marginBottom: spacing.xs },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: fontSizes.body,
    color: colors.textPrimary,
    minHeight: 48,
    backgroundColor: colors.background,
  },
  inputError: { borderColor: colors.critical },
  hint: { fontSize: fontSizes.caption, color: colors.textSecondary, marginTop: spacing.xs },
  error: { fontSize: fontSizes.caption, color: colors.critical, marginTop: spacing.xs, fontWeight: '600' },
});
