import React, { useCallback, useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { FlatList, StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body, Caption } from '../../components/Typography';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { DiscoveryCard } from './DiscoveryCard';
import { colors, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { usePreferredUnit } from '../../state/AuthContext';
import { classifyEmptyGrid, copyForEmptyGrid } from '../../domain/discoveryReality';
import type { DiscoveryCardView, RealityDashboard } from '../../api/types';
import type { DiscoveryStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<DiscoveryStackParamList, 'DiscoveryGrid'>;

export function DiscoveryGridScreen({ navigation }: Props): React.ReactElement {
  const unitPreference = usePreferredUnit();
  const gridState = useAsync(() => api.getDiscoveryGrid({ limit: 20 }), []);
  const [items, setItems] = useState<DiscoveryCardView[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [emptyMessage, setEmptyMessage] = useState<string | undefined>(undefined);
  const [dashboard, setDashboard] = useState<RealityDashboard | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  React.useEffect(() => {
    if (gridState.status !== 'ready') return;
    const { data } = gridState;
    setItems(data.items);
    setNextCursor(data.nextCursor);
    setEmptyMessage(data.message);
    if (data.items.length === 0) {
      setDashboardLoading(true);
      api
        .getRealityDashboard()
        .then(setDashboard)
        .catch(() => setDashboard(null))
        .finally(() => setDashboardLoading(false));
    } else {
      setDashboard(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gridState.status, gridState]);

  const loadMore = useCallback(async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await api.getDiscoveryGrid({ limit: 20, cursor: nextCursor });
      setItems((prev) => [...prev, ...page.items]);
      setNextCursor(page.nextCursor);
    } finally {
      setLoadingMore(false);
    }
  }, [nextCursor, loadingMore]);

  if (gridState.status === 'loading') {
    return (
      <Screen>
        <LoadingState label="Finding people near you" />
      </Screen>
    );
  }

  if (gridState.status === 'error') {
    return (
      <Screen>
        <ErrorState error={gridState.error} onRetry={gridState.reload} />
      </Screen>
    );
  }

  if (items.length === 0) {
    const reason = dashboard ? classifyEmptyGrid(dashboard) : null;
    const copy = reason ? copyForEmptyGrid(reason) : null;
    return (
      <Screen>
        <Headline style={styles.title}>Discover</Headline>
        <View style={styles.emptyBlock}>
          <Body style={styles.emptyTitle}>{copy?.title ?? 'No one new to show right now'}</Body>
          <Body style={styles.mutedText}>{copy?.message ?? emptyMessage ?? 'Check back soon.'}</Body>
          {dashboardLoading ? <Caption style={styles.mutedText}>Checking the pool near you...</Caption> : null}
          {dashboard ? (
            <View style={styles.poolBox} accessible accessibilityLabel="Your pool numbers">
              <PoolRow label="People who match your filters" value={dashboard.matchesMyFilters} />
              <PoolRow label="People whose filters you match" value={dashboard.whoseFiltersIMatch} />
              <PoolRow label="Mutual matches possible" value={dashboard.mutualMatchPool} />
            </View>
          ) : null}
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll={false} padded={false}>
      <View style={styles.header}>
        <Headline>Discover</Headline>
      </View>
      <FlatList
        data={items}
        keyExtractor={(item) => item.userId}
        numColumns={2}
        contentContainerStyle={styles.gridContent}
        columnWrapperStyle={styles.gridRow}
        renderItem={({ item }) => (
          <DiscoveryCard
            candidate={item}
            unitPreference={unitPreference}
            onPress={() => navigation.navigate('ProfileView', { userId: item.userId })}
          />
        )}
        onEndReachedThreshold={0.5}
        onEndReached={loadMore}
        ListFooterComponent={loadingMore ? <LoadingState label="Loading more" /> : null}
      />
    </Screen>
  );
}

function PoolRow({ label, value }: { label: string; value: number }): React.ReactElement {
  return (
    <View style={styles.poolRow}>
      <Caption>{label}</Caption>
      <Body style={styles.poolValue}>{value}</Body>
    </View>
  );
}

const styles = StyleSheet.create({
  header: { padding: spacing.md, paddingBottom: 0 },
  title: { marginBottom: spacing.md },
  gridContent: { padding: spacing.sm },
  gridRow: { gap: spacing.xs },
  emptyBlock: { marginTop: spacing.lg },
  emptyTitle: { fontWeight: '700', marginBottom: spacing.sm },
  mutedText: { color: colors.textSecondary, marginBottom: spacing.md },
  poolBox: { backgroundColor: colors.surface, borderRadius: 12, padding: spacing.md, gap: spacing.sm },
  poolRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  poolValue: { fontWeight: '700' },
});
