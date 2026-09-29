import { Image } from 'expo-image';
import { router } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { thumbnails } from '@/animation/thumbnails';
import { Body, Card, Heading, Screen, Tag, Title } from '@/components/ui';
import { Palette, Radius } from '@/constants/theme';
import { EXERCISES } from '@/core/exercises';
import { initialPrescription } from '@/core/progression';
import { formatLoad, useApp } from '@/store/app-store';

export default function Exercises() {
  const prescriptions = useApp((s) => s.prescriptions);
  const settings = useApp((s) => s.settings);
  return (
    <Screen>
      <Title>Exercises</Title>
      <Body muted>Tap one to watch it in 3D. Drag the figure to rotate it.</Body>
      {EXERCISES.map((e) => {
        const load = (prescriptions[e.id] ?? initialPrescription(e.id, settings.bells)).load;
        return (
          <Card key={e.id} onPress={() => router.push({ pathname: '/exercise/[id]', params: { id: e.id } })} style={styles.card}>
            <Image source={thumbnails[e.animation]} style={styles.thumb} contentFit="cover" />
            <View style={styles.text}>
              <Heading>{e.name}</Heading>
              <Body muted style={{ fontSize: 14 }}>
                {e.primary.join(' · ')}
              </Body>
              <View style={styles.tags}>
                <Tag label={e.pattern} />
                <Tag label={formatLoad(load, settings.units)} accent />
                {e.unilateral && <Tag label="per side" />}
              </View>
            </View>
          </Card>
        );
      })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  thumb: { width: 96, height: 96, borderRadius: Radius.button, backgroundColor: Palette.bg },
  text: { flex: 1, gap: 4 },
  tags: { flexDirection: 'row', gap: 6, flexWrap: 'wrap', marginTop: 2 },
});
