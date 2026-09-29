import { DarkTheme, Stack, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import { Palette } from '@/constants/theme';
import { useSession } from '@/lib/auth';
import { syncNow } from '@/lib/sync';
import { useApp } from '@/store/app-store';

SplashScreen.preventAutoHideAsync();

const theme = {
  ...DarkTheme,
  colors: { ...DarkTheme.colors, background: Palette.bg, card: Palette.bg, primary: Palette.accent, text: Palette.text },
};

export default function RootLayout() {
  const authMode = useApp((s) => s.authMode);
  const setAuthMode = useApp((s) => s.setAuthMode);
  const session = useSession();

  useEffect(() => {
    SplashScreen.hideAsync();
  }, []);

  // Returning from web OAuth, or a restored session, means account mode. Sync once signed in.
  useEffect(() => {
    if (!session) return;
    if (authMode !== 'account') setAuthMode('account');
    syncNow().catch((e) => console.warn('Sync failed', e));
  }, [session, authMode, setAuthMode]);

  return (
    <ThemeProvider value={theme}>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: Palette.bg } }}>
        <Stack.Protected guard={authMode !== undefined}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen
            name="exercise/[id]"
            options={{ headerShown: true, title: '', headerTransparent: true, headerTintColor: Palette.text }}
          />
          <Stack.Screen
            name="workout/[id]"
            options={{ headerShown: true, title: '', headerTransparent: true, headerTintColor: Palette.text }}
          />
          <Stack.Screen
            name="builder"
            options={{ headerShown: true, title: '', headerTransparent: true, headerTintColor: Palette.text }}
          />
          <Stack.Screen
            name="debug/animations"
            options={{ headerShown: true, title: '', headerTransparent: true, headerTintColor: Palette.text }}
          />
          <Stack.Screen name="session" options={{ presentation: 'fullScreenModal', gestureEnabled: false }} />
        </Stack.Protected>
        <Stack.Protected guard={authMode === undefined}>
          <Stack.Screen name="sign-in" />
        </Stack.Protected>
      </Stack>
    </ThemeProvider>
  );
}
