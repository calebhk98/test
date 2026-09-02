import React, { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { ScrollView, StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Title, Body, Caption } from '../../components/Typography';
import { Button } from '../../components/Button';
import { StatusBadge } from '../../components/StatusBadge';
import { AccessibleImage } from '../../components/AccessibleImage';
import { LoadingState, ErrorState } from '../../components/AsyncState';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { messageForError } from '../../api/errors';
import { usePreferredUnit } from '../../state/AuthContext';
import { formatDistance } from '../../units/distance';
import { messageForReasonCode } from '../../domain/capabilityCopy';
import type { DiscoveryStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<DiscoveryStackParamList, 'ProfileView'>;

const TRUST_LABELS: Record<string, { label: string; tone: 'positive' | 'neutral' | 'caution' }> = {
  new: { label: 'New member', tone: 'neutral' },
  standard: { label: 'Member', tone: 'neutral' },
  trusted: { label: 'Trusted member', tone: 'positive' },
  restricted: { label: 'Restricted', tone: 'caution' },
  high_risk: { label: 'Under review', tone: 'caution' },
};

export function ProfileViewScreen({ route }: Props): React.ReactElement {
  const { userId } = route.params;
  const unitPreference = usePreferredUnit();
  const profileState = useAsync(() => api.getPublicProfile(userId), [userId]);
  const capabilitiesState = useAsync(() => api.getMyCapabilities(), []);
  const outgoingState = useAsync(() => api.listOutgoingInterests({ limit: 50 }), []);

  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  if (profileState.status === 'loading') {
    return (
      <Screen>
        <LoadingState label="Loading profile" />
      </Screen>
    );
  }
  if (profileState.status === 'error') {
    return (
      <Screen>
        <ErrorState error={profileState.error} onRetry={profileState.reload} />
      </Screen>
    );
  }

  const profile = profileState.data;
  const distance = formatDistance(profile.approximateDistanceKm, unitPreference);
  const trust = TRUST_LABELS[profile.trustLevel] ?? { label: profile.trustLevel, tone: 'neutral' as const };

  const capability = capabilitiesState.status === 'ready' ? capabilitiesState.data.send_interest : null;
  const reasonMessage = messageForReasonCode(capability?.reasonCode);

  const sentToday =
    outgoingState.status === 'ready'
      ? outgoingState.data.items.filter((item) => isSameDay(new Date(item.createdAt), new Date())).length
      : null;

  const alreadySent = outgoingState.status === 'ready' && outgoingState.data.items.some((item) => item.counterpartUserId === userId && item.status === 'pending');

  async function handleSendInterest(): Promise<void> {
    setSending(true);
    setSendError(null);
    try {
      await api.sendInterest(userId);
      setSent(true);
    } catch (error) {
      setSendError(messageForError(error));
    } finally {
      setSending(false);
    }
  }

  const interestDisabled = sending || sent || alreadySent || capability?.allowed === false;

  return (
    <Screen>
      <ScrollView horizontal pagingEnabled showsHorizontalScrollIndicator={false} style={styles.photoScroller}>
        {profile.photoUrls.length > 0 ? (
          profile.photoUrls.map((url, index) => (
            <AccessibleImage
              key={url}
              uri={url}
              alt={`Photo ${index + 1} of ${profile.displayName}`}
              style={styles.photo}
            />
          ))
        ) : (
          <View style={[styles.photo, styles.photoPlaceholder]}>
            <Caption>No photos yet</Caption>
          </View>
        )}
      </ScrollView>

      <View style={styles.headerRow}>
        <Title>
          {profile.displayName}, {profile.age}
        </Title>
        <StatusBadge label={trust.label} tone={trust.tone} />
      </View>
      <Caption style={styles.distance}>{distance ? `${distance} away` : 'Distance unknown'}</Caption>

      {profile.bio ? <Body style={styles.bio}>{profile.bio}</Body> : null}

      {profile.visibleInterestTagNames.length > 0 ? (
        <View style={styles.tagsBlock}>
          <Body style={styles.sectionLabel}>Interests</Body>
          <View style={styles.tagRow}>
            {profile.visibleInterestTagNames.map((tag) => (
              <View key={tag} style={styles.tag}>
                <Caption style={styles.tagText}>{tag}</Caption>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      <View style={styles.interestBlock}>
        {sentToday !== null ? (
          <Caption style={styles.quota}>
            {sentToday === 0 ? "You haven't sent any interests today." : `You've sent ${sentToday} interest${sentToday === 1 ? '' : 's'} today.`}
          </Caption>
        ) : null}
        {reasonMessage ? <Caption style={styles.quota}>{reasonMessage}</Caption> : null}
        {alreadySent ? <Caption style={styles.quota}>You've already sent this person an interest.</Caption> : null}
        {sendError ? (
          <Body style={styles.error} accessibilityRole="alert">
            {sendError}
          </Body>
        ) : null}
        <Button
          label={sent ? 'Interest sent' : 'Send interest'}
          onPress={handleSendInterest}
          loading={sending}
          disabled={interestDisabled}
          accessibilityHint="Lets them know you're interested. They'll see your profile and can accept or pass."
          testID="send-interest"
        />
      </View>
    </Screen>
  );
}

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

const styles = StyleSheet.create({
  photoScroller: { height: 360, marginHorizontal: -spacing.md, marginTop: -spacing.md },
  photo: { width: 360, height: 360 },
  photoPlaceholder: { backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: spacing.md, gap: spacing.sm },
  distance: { marginTop: spacing.xs },
  bio: { marginTop: spacing.md },
  sectionLabel: { fontWeight: '700', marginBottom: spacing.sm },
  tagsBlock: { marginTop: spacing.lg },
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  tag: { backgroundColor: colors.surface, borderRadius: radii.pill, paddingHorizontal: spacing.sm, paddingVertical: spacing.xs },
  tagText: { color: colors.textPrimary, fontWeight: '600' },
  interestBlock: { marginTop: spacing.xl, gap: spacing.sm },
  quota: { color: colors.textSecondary },
  error: { color: colors.critical, fontWeight: '600' },
});
