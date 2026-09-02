import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { AccessibleImage } from '../../components/AccessibleImage';
import { Body, Caption } from '../../components/Typography';
import { colors, radii, spacing } from '../../theme/tokens';
import { formatDistance } from '../../units/distance';
import type { DiscoveryCardView, UnitPreference } from '../../api/types';

interface DiscoveryCardProps {
  candidate: DiscoveryCardView;
  unitPreference: UnitPreference;
  onPress: () => void;
}

/** No like count, no popularity badge, no boost indicator: exactly the fields the server sends, nothing inferred or added client-side (see api/types.ts DiscoveryCardView's own doc). */
export function DiscoveryCard({ candidate, unitPreference, onPress }: DiscoveryCardProps): React.ReactElement {
  const distance = formatDistance(candidate.approximateDistanceKm, unitPreference);
  const label = [
    `${candidate.displayName}, ${candidate.age}`,
    distance ? `${distance} away` : 'distance unknown',
    candidate.sharedInterestTag ? `shares an interest in ${candidate.sharedInterestTag}` : null,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <Pressable onPress={onPress} style={styles.card} accessibilityRole="button" accessibilityLabel={label} testID="discovery-card">
      <AccessibleImage
        uri={candidate.primaryPhotoUrl}
        alt={`Photo of ${candidate.displayName}`}
        style={styles.photo}
        fallback={<View style={styles.photoPlaceholder} />}
      />
      <View style={styles.info}>
        <Body style={styles.name} numberOfLines={1}>
          {candidate.displayName}, {candidate.age}
        </Body>
        <Caption numberOfLines={1}>{distance ? `${distance} away` : 'Distance unknown'}</Caption>
        {candidate.sharedInterestTag ? (
          <View style={styles.tag}>
            <Caption style={styles.tagText} numberOfLines={1}>
              {candidate.sharedInterestTag}
            </Caption>
          </View>
        ) : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { flex: 1, backgroundColor: colors.surface, borderRadius: radii.md, overflow: 'hidden', margin: spacing.xs },
  photo: { width: '100%', aspectRatio: 0.85, backgroundColor: colors.border },
  photoPlaceholder: { width: '100%', height: '100%' },
  info: { padding: spacing.sm },
  name: { fontWeight: '700' },
  tag: { alignSelf: 'flex-start', backgroundColor: colors.accentMuted, borderRadius: radii.pill, paddingHorizontal: spacing.sm, paddingVertical: 2, marginTop: spacing.xs },
  tagText: { color: colors.accent, fontWeight: '600' },
});
