import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';

import { Palette, Radius } from '@/constants/theme';
import { sortedBells } from '@/core/progression';
import { formatLoad, useApp } from '@/store/app-store';

/** Choose which of your bells an exercise uses next. Resets its progression streaks. */
export function BellPicker({ exercise, load }: { exercise: string; load: number }) {
  const settings = useApp((s) => s.settings);
  const setLoad = useApp((s) => s.setPrescriptionLoad);
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {sortedBells(settings.bells).map((kg) => (
        <Pressable key={kg} onPress={() => setLoad(exercise, kg)} style={[styles.bell, kg === load && styles.active]}>
          <Text style={[styles.text, kg === load && styles.activeText]}>{formatLoad(kg, settings.units)}</Text>
        </Pressable>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: 6 },
  bell: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: Radius.pill, backgroundColor: Palette.tonal },
  active: { backgroundColor: Palette.accent },
  text: { color: Palette.muted, fontWeight: '700' },
  activeText: { color: Palette.bg },
});
