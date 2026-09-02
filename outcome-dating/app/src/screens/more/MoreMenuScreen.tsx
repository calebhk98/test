import React from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Pressable, StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body } from '../../components/Typography';
import { colors, radii, spacing } from '../../theme/tokens';
import type { MoreStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MoreStackParamList, 'MoreMenu'>;

const ITEMS: { key: keyof MoreStackParamList; label: string; hint: string }[] = [
  { key: 'Wallet', label: 'Wallet', hint: 'Your tickets for upcoming and past dates' },
  { key: 'Stats', label: 'Your pool', hint: 'How many people match your filters' },
  { key: 'Trust', label: 'Trust', hint: 'Your trust level and how to improve it' },
  { key: 'Settings', label: 'Settings', hint: 'Units, filters, and your account' },
];

export function MoreMenuScreen({ navigation }: Props): React.ReactElement {
  return (
    <Screen>
      <Headline style={styles.title}>More</Headline>
      {ITEMS.map((item) => (
        <Pressable
          key={item.key}
          onPress={() => navigation.navigate(item.key as 'Wallet')}
          style={styles.row}
          accessibilityRole="button"
          accessibilityLabel={item.label}
          accessibilityHint={item.hint}
        >
          <View>
            <Body style={styles.label}>{item.label}</Body>
            <Body style={styles.hint}>{item.hint}</Body>
          </View>
        </Pressable>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.md },
  row: { borderWidth: 1, borderColor: colors.border, borderRadius: radii.md, padding: spacing.md, marginBottom: spacing.sm, minHeight: 48 },
  label: { fontWeight: '700' },
  hint: { color: colors.textSecondary, marginTop: 2 },
});
