import { useLocalSearchParams } from 'expo-router';
import { useMemo } from 'react';
import { View } from 'react-native';

import { clips } from '@/animation/clips';
import { BellPicker } from '@/components/bell-picker';
import { FigureViewer } from '@/components/figure-viewer';
import { Body, Card, Heading, Label, Row, Screen, Tag, Title } from '@/components/ui';
import { Palette } from '@/constants/theme';
import { getExercise } from '@/core/exercises';
import { initialPrescription } from '@/core/progression';
import { formatLoad, useApp } from '@/store/app-store';

export default function ExerciseDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const exercise = getExercise(id);
  const clip = clips[exercise.animation];
  const prescription = useApp((s) => s.prescriptions[id]) ?? initialPrescription(id, useApp.getState().settings.bells);
  const units = useApp((s) => s.settings.units);
  const sessions = useApp((s) => s.sessions);
  const recent = useMemo(
    () =>
      sessions
        .flatMap((session) => session.entries.filter((e) => e.exercise === id).map((e) => ({ ...e, date: session.startedAt })))
        .slice(0, 8),
    [sessions, id],
  );

  return (
    <Screen>
      <View style={{ height: 40 }} />
      <FigureViewer clipId={exercise.animation} />
      <Title>{exercise.name}</Title>
      <Row style={{ flexWrap: 'wrap' }}>
        {exercise.primary.map((m) => (
          <Tag key={m} label={m} accent />
        ))}
        {exercise.support.map((m) => (
          <Tag key={m} label={m} />
        ))}
      </Row>

      <Card>
        <Label>How to</Label>
        {exercise.cues.map((cue, i) => (
          <Row key={cue} style={{ alignItems: 'flex-start' }}>
            <Body style={{ color: Palette.accent, fontWeight: '800', width: 18 }}>{i + 1}</Body>
            <Body style={{ flex: 1 }}>{cue}</Body>
          </Row>
        ))}
        <Body muted style={{ fontSize: 14 }}>
          Counting: {exercise.counting}.
        </Body>
        {clip.contract?.phases && (
          <Body muted style={{ fontSize: 14 }}>
            Phases: {clip.contract.phases}.
          </Body>
        )}
      </Card>

      <Card>
        <Label>Your bell</Label>
        <BellPicker exercise={id} load={prescription.load} />
        <Body muted style={{ fontSize: 14 }}>
          Strength sets target {prescription.reps} reps next. Progression moves you up when every set tops the rep range.
        </Body>
      </Card>

      {recent.length > 0 && (
        <Card>
          <Heading>Recent sets</Heading>
          {recent.map((e, i) => (
            <Row key={i} style={{ justifyContent: 'space-between' }}>
              <Body muted>{new Date(e.date).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}</Body>
              <Body>
                {'reps' in e.target ? `${e.done} reps` : `${e.done} s`} · {formatLoad(e.load, units)}
              </Body>
            </Row>
          ))}
        </Card>
      )}
    </Screen>
  );
}
