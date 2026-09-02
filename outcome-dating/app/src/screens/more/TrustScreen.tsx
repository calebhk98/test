import React from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body, Caption } from '../../components/Typography';
import { StatusBadge } from '../../components/StatusBadge';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { ScaffoldNotice } from '../../components/ScaffoldNotice';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import type { MoreStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MoreStackParamList, 'Trust'>;

const TRUST_TONE: Record<string, 'positive' | 'neutral' | 'caution'> = {
  new: 'neutral',
  standard: 'neutral',
  trusted: 'positive',
  restricted: 'caution',
  high_risk: 'caution',
};

export function TrustScreen(_props: Props): React.ReactElement {
  const { status, data, error, reload } = useAsync(() => api.getMyTrust(), []);

  return (
    <Screen>
      <Headline style={styles.title}>Trust</Headline>
      <ScaffoldNotice remaining="The appeal flow (POST /me/trust/appeal) and trust event history are not built. This reads your real trust level and its actionable reasons." />
      {status === 'loading' ? <LoadingState label="Loading trust status" /> : null}
      {status === 'error' ? <ErrorState error={error} onRetry={reload} /> : null}
      {status === 'ready' ? (
        <View>
          <StatusBadge label={data.trustLevel} tone={TRUST_TONE[data.trustLevel] ?? 'neutral'} />
          {data.actionableImprovements.length > 0 ? (
            <View style={styles.section}>
              <Body style={styles.sectionLabel}>Things that would help</Body>
              {data.actionableImprovements.map((item) => (
                <Caption key={item} style={styles.item}>
                  {'•'} {item}
                </Caption>
              ))}
            </View>
          ) : null}
          {data.recentNegativeEvents.length > 0 ? (
            <View style={styles.section}>
              <Body style={styles.sectionLabel}>Recent events</Body>
              {data.recentNegativeEvents.map((item) => (
                <Caption key={item} style={styles.item}>
                  {'•'} {item}
                </Caption>
              ))}
            </View>
          ) : null}
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.sm },
  section: { marginTop: spacing.lg, backgroundColor: colors.surface, borderRadius: radii.md, padding: spacing.md },
  sectionLabel: { fontWeight: '700', marginBottom: spacing.sm },
  item: { marginBottom: spacing.xs },
});
