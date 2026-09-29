import { TabList, TabSlot, TabTrigger, Tabs, type TabTriggerSlotProps } from 'expo-router/ui';
import { SymbolView } from 'expo-symbols';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Palette, Radius } from '@/constants/theme';

import { TABS } from './tabs';

export default function AppTabs() {
  return (
    <Tabs>
      <TabSlot style={{ height: '100%' }} />
      <TabList style={styles.bar}>
        {TABS.map((tab) => (
          <TabTrigger key={tab.name} name={tab.name} href={tab.name === 'index' ? '/' : `/${tab.name}`} asChild>
            <TabButton icon={tab.web}>{tab.label}</TabButton>
          </TabTrigger>
        ))}
      </TabList>
    </Tabs>
  );
}

function TabButton({ children, isFocused, icon, ...props }: TabTriggerSlotProps & { icon: string }) {
  const color = isFocused ? Palette.accent : Palette.muted;
  return (
    <Pressable {...props} style={({ pressed }) => [styles.button, pressed && { opacity: 0.7 }]}>
      <View style={[styles.pill, isFocused && styles.pillActive]}>
        <SymbolView name={{ web: icon as never }} tintColor={color} size={22} />
      </View>
      <Text style={[styles.label, { color: isFocused ? Palette.text : Palette.muted }]}>{children}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    backgroundColor: 'rgba(0,0,0,0.92)',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Palette.track,
    paddingVertical: 8,
  },
  button: { flex: 1, maxWidth: 120, alignItems: 'center', gap: 3 },
  pill: { paddingHorizontal: 16, paddingVertical: 4, borderRadius: Radius.pill },
  pillActive: { backgroundColor: Palette.tonal },
  label: { fontSize: 12, fontWeight: '600' },
});
