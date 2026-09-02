/**
 * Token storage. Tokens live in the device's secure keychain
 * (expo-secure-store), never in AsyncStorage, and never anywhere in
 * component state that could end up in a screenshot-adjacent dev tool.
 * `api/client.ts` is the only module that reads or writes this.
 */
import * as SecureStore from 'expo-secure-store';
import type { AuthTokens } from './types';

const ACCESS_KEY = 'outcome_dating.access_token';
const REFRESH_KEY = 'outcome_dating.refresh_token';

export async function saveTokens(tokens: AuthTokens): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_KEY, tokens.accessToken);
  await SecureStore.setItemAsync(REFRESH_KEY, tokens.refreshToken);
}

export async function loadTokens(): Promise<{ accessToken: string; refreshToken: string } | null> {
  const [accessToken, refreshToken] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_KEY),
    SecureStore.getItemAsync(REFRESH_KEY),
  ]);
  if (!accessToken || !refreshToken) return null;
  return { accessToken, refreshToken };
}

export async function clearTokens(): Promise<void> {
  await Promise.all([SecureStore.deleteItemAsync(ACCESS_KEY), SecureStore.deleteItemAsync(REFRESH_KEY)]);
}
