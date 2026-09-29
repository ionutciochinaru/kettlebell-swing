import { Body, Label, Screen, Title } from '@/components/ui';
import { WorkoutCard } from '@/components/workout-card';
import { BLOCK_LABELS, PRESET_WORKOUTS, type BlockKind } from '@/core/workouts';
import { useApp } from '@/store/app-store';

const ORDER: BlockKind[] = ['sets', 'circuit', 'emom', 'amrap', 'intervals', 'ladder'];

export default function Workouts() {
  const custom = useApp((s) => s.customWorkouts);
  const all = [...PRESET_WORKOUTS, ...custom];
  return (
    <Screen>
      <Title>Workouts</Title>
      <Body muted>Pick a training type. Loads come from your progression and the bells you own.</Body>
      {ORDER.map((kind) => {
        const matching = all.filter((w) => w.blocks[0]?.kind === kind);
        if (!matching.length) return null;
        return [
          <Label key={`${kind}-label`}>{BLOCK_LABELS[kind]}</Label>,
          ...matching.map((w) => <WorkoutCard key={w.id} workout={w} />),
        ];
      })}
    </Screen>
  );
}
