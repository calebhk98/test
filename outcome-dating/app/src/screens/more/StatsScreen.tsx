import React from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body, Caption } from '../../components/Typography';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { ScaffoldNotice } from '../../components/ScaffoldNotice';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import type { MoreStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MoreStackParamList, 'Stats'>;

function suppressibleLabel(v: { value: number | null; suppressed: boolean }): string {
  if (v.suppressed) return 'Hidden (too few people to show without identifying someone)';
  return v.value === null ? 'Unknown' : String(v.value);
}

export function StatsScreen(_props: Props): React.ReactElement {
  const result = useAsync(() => api.getMyFilterCosts(), []);

  return (
    <Screen>
      <Headline style={styles.title}>Your pool</Headline>
      <ScaffoldNotice remaining="The pool Venn diagram (GET /me/stats/venn.svg), trend charts, and photo-performance stats are not built yet. This reads the real filter-cost numbers." />
      {result.status === 'loading' ? <LoadingState label="Loading your stats" /> : null}
      {result.status === 'error' ? <ErrorState error={result.error} onRetry={result.reload} /> : null}
      {result.status === 'ready' ? (
        <View style={styles.box}>
          <Row label="People who match your filters" value={suppressibleLabel(result.data.currentPool)} />
          <Row label="People whose filters you match" value={suppressibleLabel(result.data.whoseFiltersIMatch)} />
          <Row label="Mutual matches possible" value={suppressibleLabel(result.data.mutualMatchPool)} />
          {result.data.costliestFilter ? (
            <Caption style={styles.note}>
              Your costliest filter is "{result.data.costliestFilter.filterKey}": removing it would add
              {' '}
              {suppressibleLabel(result.data.costliestFilter.additionalCandidatesIfRemoved)} candidates.
            </Caption>
          ) : null}
        </View>
      ) : null}
    </Screen>
  );
}

function Row({ label, value }: { label: string; value: string }): React.ReactElement {
  return (
    <View style={styles.row}>
      <Body>{label}</Body>
      <Body style={styles.value}>{value}</Body>
    </View>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.sm },
  box: { backgroundColor: colors.surface, borderRadius: radii.md, padding: spacing.md, gap: spacing.md },
  row: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.sm },
  value: { fontWeight: '700', flexShrink: 1, textAlign: 'right' },
  note: { marginTop: spacing.sm },
});
