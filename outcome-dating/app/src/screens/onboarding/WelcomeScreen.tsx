import React from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, View } from 'react-native';
import { Screen } from '../../components/Screen';
import { Headline, Body } from '../../components/Typography';
import { Button } from '../../components/Button';
import { spacing } from '../../theme/tokens';
import type { AuthStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AuthStackParamList, 'Welcome'>;

export function WelcomeScreen({ navigation }: Props): React.ReactElement {
  return (
    <Screen>
      <View style={styles.content}>
        <Headline>Outcome Dating</Headline>
        <Body style={styles.subtitle}>
          Answer real questions, meet people who actually match what you want, and go on dates, not chats that never
          end.
        </Body>
        <View style={styles.actions}>
          <Button label="Create an account" onPress={() => navigation.navigate('SignUp')} />
          <Button label="I already have an account" onPress={() => navigation.navigate('Login')} variant="secondary" />
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: { flex: 1, justifyContent: 'center', gap: spacing.lg },
  subtitle: { marginBottom: spacing.lg },
  actions: { gap: spacing.md },
});
