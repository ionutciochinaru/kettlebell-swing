import { Image } from 'expo-image';
import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';

import { thumbnails } from '@/animation/thumbnails';
import { Palette, Radius } from '@/constants/theme';
import { EXERCISES } from '@/core/exercises';

/** Horizontal strip of exercise thumbnails; the selected one is outlined in orange. */
export function ExercisePicker({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {EXERCISES.map((e) => {
        const selected = e.id === value;
        return (
          <Pressable
            key={e.id}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            onPress={() => onChange(e.id)}
            style={[styles.item, selected && styles.selected]}>
            <Image source={thumbnails[e.animation]} style={styles.thumb} contentFit="cover" />
            <Text style={[styles.name, selected && styles.selectedName]} numberOfLines={2}>
              {e.name}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: 8, paddingVertical: 2 },
  item: { width: 88, borderRadius: Radius.button, padding: 4, borderWidth: 2, borderColor: 'transparent', gap: 4 },
  selected: { borderColor: Palette.accent },
  thumb: { width: '100%', aspectRatio: 1, borderRadius: Radius.button - 4, backgroundColor: Palette.bg },
  name: { color: Palette.muted, fontSize: 12, fontWeight: '600', textAlign: 'center' },
  selectedName: { color: Palette.text },
});
