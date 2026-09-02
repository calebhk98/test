import React from 'react';
import { ScrollView, StyleSheet, View, ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, spacing } from '../theme/tokens';

interface ScreenProps {
  children: React.ReactNode;
  scroll?: boolean;
  style?: ViewStyle;
  padded?: boolean;
}

/** Base screen chrome: safe-area aware, off-white ground, optional scroll. Every built screen renders inside one of these instead of a bare View, so safe-area and background stay consistent. */
export function Screen({ children, scroll = true, style, padded = true }: ScreenProps): React.ReactElement {
  const Container = scroll ? ScrollView : View;
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <Container
        style={styles.flex}
        contentContainerStyle={scroll ? [padded && styles.padded, style] : undefined}
        {...(scroll ? { keyboardShouldPersistTaps: 'handled' as const } : {})}
      >
        <View style={!scroll ? [styles.flex, padded && styles.padded, style] : undefined}>{children}</View>
      </Container>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  flex: { flex: 1 },
  padded: { padding: spacing.md, flexGrow: 1 },
});
