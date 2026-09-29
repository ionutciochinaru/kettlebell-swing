import '@/global.css';

import { Platform } from 'react-native';

/** Watch palette (design/visual-tokens.json): black stage, ivory text, orange accent. */
export const Palette = {
  bg: '#000000',
  stage: '#0b0b0a',
  panel: '#151514',
  pressed: '#30302c',
  text: '#eeede4',
  muted: '#a6a69e',
  dim: '#66665f',
  track: '#32322e',
  accent: '#ff6b2b',
  accentPressed: '#da5720',
  primaryFill: '#c94a16',
  primaryPressed: '#a63c10',
  onPrimary: '#ffffff',
  go: '#00a600',
  goPressed: '#008500',
  danger: '#c52e32',
  tonal: '#30312b',
  tonalPressed: '#45473d',
} as const;

export const Spacing = { half: 2, one: 4, two: 8, three: 16, four: 24, five: 32, six: 64 } as const;

export const Radius = { card: 18, button: 14, pill: 999 } as const;

export const Fonts = Platform.select({
  ios: { sans: 'system-ui', rounded: 'ui-rounded', mono: 'ui-monospace' },
  web: { sans: 'var(--font-display)', rounded: 'var(--font-rounded)', mono: 'var(--font-mono)' },
  default: { sans: 'normal', rounded: 'normal', mono: 'monospace' },
});

export const MaxContentWidth = 720;
