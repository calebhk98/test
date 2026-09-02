import React, { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { FlatList, KeyboardAvoidingView, Platform, StyleSheet, TextInput, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Body } from '../../components/Typography';
import { Button } from '../../components/Button';
import { LoadingState, ErrorState, EmptyState } from '../../components/AsyncState';
import { colors, radii, spacing } from '../../theme/tokens';
import { useAsync } from '../../hooks/useAsync';
import { api } from '../../api/client';
import { messageForError } from '../../api/errors';
import { useAuth } from '../../state/AuthContext';
import { TimelineEventRow } from './TimelineEventRow';
import type { TimelineEventView } from '../../api/types';
import type { MatchesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<MatchesStackParamList, 'Conversation'>;

export function ConversationScreen({ route, navigation }: Props): React.ReactElement {
  const { conversationId, displayName } = route.params;
  const { me } = useAuth();
  const timelineState = useAsync(() => api.getConversationTimeline(conversationId, { limit: 50 }), [conversationId]);
  const [events, setEvents] = useState<TimelineEventView[]>([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  React.useEffect(() => {
    if (timelineState.status === 'ready') {
      setEvents([...timelineState.data.items].sort((a, b) => a.occurredAt.localeCompare(b.occurredAt)));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timelineState.status, timelineState]);

  React.useLayoutEffect(() => {
    navigation.setOptions({ title: displayName });
  }, [navigation, displayName]);

  async function handleSend(): Promise<void> {
    const body = draft.trim();
    if (!body) return;
    setSending(true);
    setSendError(null);
    try {
      await api.sendMessage(conversationId, body);
      setDraft('');
      const refreshed = await api.getConversationTimeline(conversationId, { limit: 50 });
      setEvents([...refreshed.items].sort((a, b) => a.occurredAt.localeCompare(b.occurredAt)));
    } catch (err) {
      setSendError(messageForError(err));
    } finally {
      setSending(false);
    }
  }

  if (timelineState.status === 'loading') {
    return (
      <Screen>
        <LoadingState label="Loading conversation" />
      </Screen>
    );
  }
  if (timelineState.status === 'error') {
    return (
      <Screen>
        <ErrorState error={timelineState.error} onRetry={timelineState.reload} />
      </Screen>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Screen scroll={false} padded={false}>
        <View style={styles.proposeRow}>
          <Button
            label="Propose a date"
            onPress={() => navigation.navigate('ProposeDate', { conversationId, recipientDisplayName: displayName })}
            variant="secondary"
            testID="propose-date"
          />
        </View>
        {events.length === 0 ? (
          <EmptyState title="Say hello" message={`Start the conversation with ${displayName}.`} />
        ) : (
          <FlatList
            data={events}
            keyExtractor={(item) => `${item.kind}-${item.id}`}
            contentContainerStyle={styles.listContent}
            renderItem={({ item }) => (
              <TimelineEventRow
                event={item}
                isOwnMessage={item.kind === 'message' && item.senderId === me?.id}
                viewerId={me?.id}
                onPressDateProposal={(dateProposalId) => navigation.navigate('DateProposalDetail', { dateProposalId })}
              />
            )}
          />
        )}
        {sendError ? (
          <Body style={styles.error} accessibilityRole="alert">
            {sendError}
          </Body>
        ) : null}
        <View style={styles.composer}>
          <TextInput
            value={draft}
            onChangeText={setDraft}
            placeholder="Message"
            placeholderTextColor={colors.textSecondary}
            style={styles.input}
            multiline
            accessibilityLabel="Message"
            editable={!sending}
          />
          <Button label="Send" onPress={handleSend} loading={sending} disabled={!draft.trim()} testID="send-message" />
        </View>
      </Screen>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  proposeRow: { padding: spacing.md, paddingBottom: 0, alignItems: 'flex-start' },
  listContent: { padding: spacing.md },
  error: { color: colors.critical, fontWeight: '600', marginHorizontal: spacing.md },
  composer: { flexDirection: 'row', gap: spacing.sm, padding: spacing.md, alignItems: 'flex-end' },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 48,
    maxHeight: 120,
    color: colors.textPrimary,
  },
});
