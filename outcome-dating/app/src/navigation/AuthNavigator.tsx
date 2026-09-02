import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { WelcomeScreen } from '../screens/onboarding/WelcomeScreen';
import { SignUpScreen } from '../screens/onboarding/SignUpScreen';
import { LoginScreen } from '../screens/onboarding/LoginScreen';
import type { AuthStackParamList } from './types';

const Stack = createNativeStackNavigator<AuthStackParamList>();

export function AuthNavigator(): React.ReactElement {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="SignUp" component={SignUpScreen} options={{ headerShown: true, title: 'Create account' }} />
      <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: true, title: 'Sign in' }} />
    </Stack.Navigator>
  );
}
