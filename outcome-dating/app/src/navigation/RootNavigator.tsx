import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { LoadingState } from '../components/AsyncState';
import { Screen } from '../components/Screen';
import { useAuth } from '../state/AuthContext';

export function RootNavigator(): React.ReactElement {
  const { status } = useAuth();

  if (status === 'loading') {
    return (
      <Screen>
        <LoadingState label="Loading Outcome Dating" />
      </Screen>
    );
  }

  return <NavigationContainer>{status === 'signedIn' ? <MainNavigator /> : <AuthNavigator />}</NavigationContainer>;
}
