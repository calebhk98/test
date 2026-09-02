import React from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { FlatList, Pressable, StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body, Caption } from '../../components/Typography';
import { LoadingState, ErrorState, EmptyState } from '../../components/AsyncState';
import { AccessibleImage } from '../../components/AccessibleImage';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { usePreferredUnit } from '../../state/AuthContext';
import { formatDistance } from '../../units/distance';
import { formatDateTime } from '../../units/datetime';
import type { MatchListItemView } from '../../api/types';
import type { MatchesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MatchesStackParamList, 'MatchesList'>;

export function MatchesListScreen({ navigation }: Props): React.ReactElement {
  const unitPreference = usePreferredUnit();
  const { status, data, error, reload } = useAsync(() => api.listMatches({ limit: 50 }), []);

  if (status === 'loading') {
    return (
      <Screen>
        <LoadingState label="Loading matches" />
      </Screen>
    );
  }
  if (status === 'error') {
    return (
      <Screen>
        <ErrorState error={error} onRetry={reload} />
      </Screen>
    );
  }
  if (data.items.length === 0) {
    return (
      <Screen>
        <Headline style={styles.title}>Matches</Headline>
        <EmptyState
          title="No matches yet"
          message="When you and someone else both accept an interest, you'll see them here and can start talking."
        />
      </Screen>
    );
  }

  return (
    <Screen scroll={false} padded={false}>
      <View style={styles.header}>
        <Headline>Matches</Headline>
      </View>
      <FlatList
        data={data.items}
        keyExtractor={(item) => item.conversationId}
        renderItem={({ item }) => (
          <MatchRow
            match={item}
            unitPreference={unitPreference}
            onPress={() => navigation.navigate('Conversation', { conversationId: item.conversationId, displayName: item.displayName })}
          />
        )}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        contentContainerStyle={styles.listContent}
      />
    </Screen>
  );
}

function MatchRow({
  match,
  unitPreference,
  onPress,
}: {
  match: MatchListItemView;
  unitPreference: ReturnType<typeof usePreferredUnit>;
  onPress: () => void;
}): React.ReactElement {
  const distance = formatDistance(match.approximateDistanceKm, unitPreference);
  const label = [
    match.displayName,
    match.unreadCount > 0 ? `${match.unreadCount} unread message${match.unreadCount === 1 ? '' : 's'}` : null,
    match.lastMessagePreview,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <Pressable onPress={onPress} style={styles.row} accessibilityRole="button" accessibilityLabel={label} testID="match-row">
      <AccessibleImage uri={match.primaryPhotoUrl} alt={`Photo of ${match.displayName}`} style={styles.avatar} />
      <View style={styles.rowText}>
        <View style={styles.rowTop}>
          <Body style={styles.name}>{match.displayName}</Body>
          {match.lastMessageAt ? <Caption>{formatDateTime(match.lastMessageAt)}</Caption> : null}
        </View>
        <Caption numberOfLines={1} style={styles.preview}>
          {match.lastMessagePreview ?? (distance ? `${distance} away` : 'Say hello')}
        </Caption>
      </View>
      {match.unreadCount > 0 ? (
        <View style={styles.unreadBadge} accessibilityElementsHidden importantForAccessibility="no">
          <Caption style={styles.unreadText}>{match.unreadCount}</Caption>
        </View>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  header: { padding: spacing.md, paddingBottom: 0 },
  title: { marginBottom: spacing.md },
  listContent: { paddingHorizontal: spacing.md },
  separator: { height: 1, backgroundColor: colors.border },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md },
  avatar: { width: 56, height: 56, borderRadius: radii.pill, backgroundColor: colors.border },
  rowText: { flex: 1 },
  rowTop: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.sm },
  name: { fontWeight: '700' },
  preview: { marginTop: 2 },
  unreadBadge: { backgroundColor: colors.accent, borderRadius: radii.pill, minWidth: 22, height: 22, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 6 },
  unreadText: { color: colors.textOnAccent, fontWeight: '700' },
});
