import React from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { Body, Title } from './Typography';
import { Button } from './Button';
import { colors, spacing } from '../theme/tokens';
import { isOffline, messageForError } from '../api/errors';

interface LoadingProps {
  label?: string;
}

export function LoadingState({ label = 'Loading' }: LoadingProps): React.ReactElement {
  return (
    <View style={styles.center} accessibilityRole="progressbar" accessibilityLabel={label}>
      <ActivityIndicator size="large" color={colors.accent} />
      <Body style={styles.mutedText}>{label}</Body>
    </View>
  );
}

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
}

export function ErrorState({ error, onRetry }: ErrorStateProps): React.ReactElement {
  const offline = isOffline(error);
  return (
    <View style={styles.center} accessibilityRole="alert">
      <Title style={styles.centerText}>{offline ? "You're offline" : 'Something went wrong'}</Title>
      <Body style={[styles.mutedText, styles.centerText]}>{messageForError(error)}</Body>
      {onRetry ? <Button label="Try again" onPress={onRetry} variant="secondary" /> : null}
    </View>
  );
}

interface EmptyStateProps {
  title: string;
  message?: string;
  action?: { label: string; onPress: () => void };
}

export function EmptyState({ title, message, action }: EmptyStateProps): React.ReactElement {
  return (
    <View style={styles.center}>
      <Title style={styles.centerText}>{title}</Title>
      {message ? <Body style={[styles.mutedText, styles.centerText]}>{message}</Body> : null}
      {action ? <Button label={action.label} onPress={action.onPress} variant="secondary" /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, gap: spacing.sm },
  mutedText: { color: colors.textSecondary },
  centerText: { textAlign: 'center' },
});
