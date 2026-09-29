import { NativeTabs } from 'expo-router/unstable-native-tabs';

import { Palette } from '@/constants/theme';

import { TABS } from './tabs';

export default function AppTabs() {
  return (
    <NativeTabs
      backgroundColor={Palette.bg}
      indicatorColor={Palette.tonal}
      iconColor={{ default: Palette.muted, selected: Palette.accent }}
      labelStyle={{ default: { color: Palette.muted }, selected: { color: Palette.text } }}>
      {TABS.map((tab) => (
        <NativeTabs.Trigger key={tab.name} name={tab.name}>
          <NativeTabs.Trigger.Label>{tab.label}</NativeTabs.Trigger.Label>
          <NativeTabs.Trigger.Icon sf={tab.sf} md={tab.md} />
        </NativeTabs.Trigger>
      ))}
    </NativeTabs>
  );
}
