import React, { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body, Caption } from '../../components/Typography';
import { Button } from '../../components/Button';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { ScaffoldNotice } from '../../components/ScaffoldNotice';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { messageForError } from '../../api/errors';
import { useAuth } from '../../state/AuthContext';
import type { UnitPreference } from '../../api/types';
import type { MoreStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MoreStackParamList, 'Settings'>;

export function SettingsScreen(_props: Props): React.ReactElement {
  const { profile, refreshProfile, logout } = useAuth();
  const filtersState = useAsync(() => api.getMyFilters(), []);
  const [savingUnit, setSavingUnit] = useState(false);
  const [unitError, setUnitError] = useState<string | null>(null);

  async function setUnit(unitPreference: UnitPreference): Promise<void> {
    if (profile?.unitPreference === unitPreference) return;
    setSavingUnit(true);
    setUnitError(null);
    try {
      await api.updateMyProfile({ unitPreference });
      await refreshProfile();
    } catch (error) {
      setUnitError(messageForError(error));
    } finally {
      setSavingUnit(false);
    }
  }

  return (
    <Screen>
      <Headline style={styles.title}>Settings</Headline>

      <View style={styles.section}>
        <Body style={styles.sectionLabel}>Units</Body>
        <View style={styles.unitRow}>
          <Button
            label="Kilometres / metric"
            onPress={() => setUnit('metric')}
            variant={profile?.unitPreference === 'metric' ? 'primary' : 'secondary'}
            loading={savingUnit && profile?.unitPreference !== 'metric'}
          />
          <Button
            label="Miles / imperial"
            onPress={() => setUnit('imperial')}
            variant={profile?.unitPreference === 'imperial' ? 'primary' : 'secondary'}
            loading={savingUnit && profile?.unitPreference !== 'imperial'}
          />
        </View>
        {unitError ? (
          <Body style={styles.error} accessibilityRole="alert">
            {unitError}
          </Body>
        ) : null}
      </View>

      <View style={styles.section}>
        <Body style={styles.sectionLabel}>Filters</Body>
        <ScaffoldNotice remaining="Editing filters (PATCH /me/filters) is not built, only a read-only list. Notification preferences and the cleanup-preview flow are also not built." />
        {filtersState.status === 'loading' ? <LoadingState label="Loading filters" /> : null}
        {filtersState.status === 'error' ? <ErrorState error={filtersState.error} onRetry={filtersState.reload} /> : null}
        {filtersState.status === 'ready' ? (
          <View style={styles.filterBox}>
            {filtersState.data.length === 0 ? (
              <Caption>No filters set.</Caption>
            ) : (
              filtersState.data.map((f) => (
                <Caption key={f.filterKey} style={styles.filterRow}>
                  {f.filterKey} {f.operator} {JSON.stringify(f.value)} {f.enabled ? '' : '(disabled)'}
                </Caption>
              ))
            )}
          </View>
        ) : null}
      </View>

      <View style={styles.section}>
        <Button label="Sign out" onPress={logout} variant="destructive" testID="sign-out" />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.md },
  section: { marginBottom: spacing.xl },
  sectionLabel: { fontWeight: '700', marginBottom: spacing.sm },
  unitRow: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  error: { color: colors.critical, fontWeight: '600', marginTop: spacing.sm },
  filterBox: { backgroundColor: colors.surface, borderRadius: radii.md, padding: spacing.md, gap: spacing.xs },
  filterRow: { fontFamily: 'monospace' },
});
