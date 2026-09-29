import { EXERCISES } from '../exercises';
import { applyProgression, type SetEntry } from '../session';
import { compileWorkout, type LoadPlan, type WorkStep } from '../timeline';
import { PRESET_WORKOUTS, getWorkout, workoutExercises, type Workout } from '../workouts';
import { clips } from '../../animation/clips';

const plan: LoadPlan = { load: () => 16, reps: (_, [min]) => min };
const work = (steps: ReturnType<typeof compileWorkout>) => steps.filter((s): s is WorkStep => s.kind === 'work');

describe('compileWorkout', () => {
  it('interleaves rests between sets but not after the last set', () => {
    const w: Workout = { id: 't', name: 't', summary: '', blocks: [{ kind: 'sets', exercise: 'kb-swing', sets: 3, repRange: [10, 15], rest: 60 }] };
    const steps = compileWorkout(w, plan);
    expect(steps.map((s) => s.kind)).toEqual(['work', 'rest', 'work', 'rest', 'work']);
    expect(work(steps)[0]).toMatchObject({ mode: 'reps', target: { reps: 10 }, load: 16 });
  });

  it('builds circuits round by round with station and round rests', () => {
    const steps = compileWorkout(getWorkout('full-body-circuit')!, plan);
    expect(work(steps)).toHaveLength(20);
    expect(steps.filter((s) => s.kind === 'rest' && s.label === 'Rest between rounds')).toHaveLength(3);
    expect(steps.at(-1)?.kind).toBe('work');
  });

  it('gives EMOM minutes a fixed 60 s window', () => {
    const steps = work(compileWorkout(getWorkout('swing-emom')!, plan));
    expect(steps).toHaveLength(10);
    expect(steps.every((s) => s.mode === 'window' && s.duration === 60)).toBe(true);
  });

  it('turns Tabata into timed work and short rests', () => {
    const steps = compileWorkout(getWorkout('tabata-swings')!, plan);
    expect(work(steps).every((s) => s.mode === 'timed' && s.duration === 20)).toBe(true);
    expect(steps.filter((s) => s.kind === 'rest')).toHaveLength(7);
  });

  it('counts ladders up and down', () => {
    const reps = work(compileWorkout(getWorkout('swing-ladder')!, plan)).map((s) => ('reps' in s.target ? s.target.reps : 0));
    expect(reps).toEqual([5, 10, 15, 20, 15, 10, 5]);
  });

  it('keeps an AMRAP as one step with resolved loads', () => {
    const [step] = compileWorkout(getWorkout('amrap-12')!, plan);
    expect(step).toMatchObject({ kind: 'amrap', duration: 720 });
  });

  it('adds a transition rest between blocks', () => {
    const steps = compileWorkout(getWorkout('swing-foundations')!, plan);
    expect(steps.filter((s) => s.kind === 'rest' && s.label === 'Next block')).toHaveLength(2);
  });
});

describe('catalogue integrity', () => {
  it('every preset uses known exercises and every exercise has a 3D clip', () => {
    const ids = new Set(EXERCISES.map((e) => e.id));
    for (const w of PRESET_WORKOUTS) for (const e of workoutExercises(w)) expect(ids.has(e)).toBe(true);
    for (const e of EXERCISES) expect(clips[e.animation]?.frames.length).toBeGreaterThan(0);
  });
});

describe('applyProgression', () => {
  it('uses double progression for sets and effort for other blocks', () => {
    const workout: Workout = {
      id: 'mix',
      name: 'mix',
      summary: '',
      blocks: [
        { kind: 'sets', exercise: 'kb-swing', sets: 2, repRange: [10, 15], rest: 60 },
        { kind: 'emom', minutes: 2, stations: [{ exercise: 'goblet-squat', target: { reps: 8 } }] },
      ],
    };
    const entries: SetEntry[] = [
      { exercise: 'kb-swing', blockKind: 'sets', block: 0, load: 16, target: { reps: 15 }, done: 15 },
      { exercise: 'kb-swing', blockKind: 'sets', block: 0, load: 16, target: { reps: 15 }, done: 15 },
      { exercise: 'goblet-squat', blockKind: 'emom', block: 1, load: 12, target: { reps: 8 }, done: 8 },
    ];
    const current = {
      'kb-swing': { load: 16, reps: 15, missStreak: 0, easyStreak: 0 },
      'goblet-squat': { load: 12, reps: 8, missStreak: 0, easyStreak: 1 },
    };
    const { prescriptions, progress } = applyProgression(workout, entries, { 'kb-swing': 'good', 'goblet-squat': 'easy' }, current, [8, 12, 16, 20]);
    expect(prescriptions['kb-swing']).toMatchObject({ load: 20, reps: 10 });
    expect(prescriptions['goblet-squat'].load).toBe(16);
    expect(progress['kb-swing'].change).toBe('load-up');
  });
});
