/**
 * Session state: who is signed in, and their profile (the source of
 * `unitPreference`, read by every distance/height/weight formatter
 * through `usePreferences` below). One provider at the root of the
 * app; every screen reads from here instead of holding its own copy of
 * "am I signed in".
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { messageForError } from '../api/errors';
import type { LoginInput, MeView, MyProfileView, RegisterInput, UnitPreference } from '../api/types';

type SessionStatus = 'loading' | 'signedOut' | 'signedIn';

interface AuthContextValue {
  status: SessionStatus;
  me: MeView | null;
  profile: MyProfileView | null;
  register: (input: RegisterInput) => Promise<void>;
  login: (input: LoginInput) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  lastError: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }): React.ReactElement {
  const [status, setStatus] = useState<SessionStatus>('loading');
  const [me, setMe] = useState<MeView | null>(null);
  const [profile, setProfile] = useState<MyProfileView | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  const loadSession = useCallback(async () => {
    try {
      const [meResult, profileResult] = await Promise.all([api.getMe(), api.getMyProfile()]);
      setMe(meResult);
      setProfile(profileResult);
      setStatus('signedIn');
    } catch {
      await api.signOut();
      setStatus('signedOut');
    }
  }, []);

  useEffect(() => {
    api.restoreSession().then((hasSession) => {
      if (hasSession) {
        void loadSession();
      } else {
        setStatus('signedOut');
      }
    });
  }, [loadSession]);

  useEffect(() => {
    return api.onUnauthorized(() => {
      setMe(null);
      setProfile(null);
      setStatus('signedOut');
    });
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    setLastError(null);
    try {
      const user = await api.register(input);
      setMe(user);
      const profileResult = await api.getMyProfile().catch(() => null);
      setProfile(profileResult);
      setStatus('signedIn');
    } catch (error) {
      setLastError(messageForError(error));
      throw error;
    }
  }, []);

  const login = useCallback(async (input: LoginInput) => {
    setLastError(null);
    try {
      const user = await api.login(input);
      setMe(user);
      const profileResult = await api.getMyProfile().catch(() => null);
      setProfile(profileResult);
      setStatus('signedIn');
    } catch (error) {
      setLastError(messageForError(error));
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setMe(null);
    setProfile(null);
    setStatus('signedOut');
  }, []);

  const refreshProfile = useCallback(async () => {
    const profileResult = await api.getMyProfile().catch(() => null);
    if (profileResult) setProfile(profileResult);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, me, profile, register, login, logout, refreshProfile, lastError }),
    [status, me, profile, register, login, logout, refreshProfile, lastError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

/** The one place a screen should ask "what unit does this person want". Falls back to metric before a profile has loaded, matching the backend's own documented default. */
export function usePreferredUnit(): UnitPreference {
  const { profile } = useAuth();
  return profile?.unitPreference ?? 'metric';
}
