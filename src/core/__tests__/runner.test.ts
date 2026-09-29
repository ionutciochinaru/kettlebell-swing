import { elapsed, remaining, runnerReducer, startRunner, type RunnerState } from '../runner';
import { compileWorkout, type LoadPlan } from '../timeline';
import { getWorkout, type Workout } from '../workouts';

const plan: LoadPlan = { load: () => 16, reps: (_, [min]) => min };
const run = (state: RunnerState, ...actions: Parameters<typeof runnerReducer>[1][]) => actions.reduce(runnerReducer, state);

describe('runner', () => {
  const sets: Workout = { id: 's', name: 's', summary: '', blocks: [{ kind: 'sets', exercise: 'kb-swing', sets: 2, repRange: [10, 15], rest: 60 }] };

  it('reviews reps after Done and logs the corrected amount', () => {
    let s = startRunner(compileWorkout(sets, plan), 0);
    s = run(s, { type: 'done', now: 20_000 }, { type: 'adjust', delta: -2 }, { type: 'confirm', now: 21_000 });
    expect(s.entries).toEqual([expect.objectContaining({ exercise: 'kb-swing', done: 8, load: 16 })]);
    expect(s.index).toBe(1);
  });

  it('auto-advances rest when it runs out, including extensions', () => {
    let s = startRunner(compileWorkout(sets, plan), 0);
    s = run(s, { type: 'done', now: 1000 }, { type: 'confirm', now: 1000 }, { type: 'extendRest', seconds: 15 });
    expect(run(s, { type: 'tick', now: 61_000 }).index).toBe(1);
    expect(run(s, { type: 'tick', now: 76_000 }).index).toBe(2);
  });

  it('pausing freezes the clock', () => {
    let s = startRunner(compileWorkout(getWorkout('tabata-swings')!, plan), 0);
    s = run(s, { type: 'pause', now: 5000 }, { type: 'tick', now: 60_000 });
    expect(s.index).toBe(0);
    expect(elapsed(s, 60_000)).toBe(5);
    s = run(s, { type: 'resume', now: 60_000 });
    expect(remaining(s, 60_000)).toBe(15);
  });

  it('logs timed intervals automatically at full duration', () => {
    let s = startRunner(compileWorkout(getWorkout('tabata-swings')!, plan), 0);
    s = run(s, { type: 'tick', now: 20_000 });
    expect(s.entries[0]).toMatchObject({ done: 20, target: { seconds: 20 } });
  });

  it('EMOM: Done logs once, window keeps running; unlogged minutes count as done, skip records a miss', () => {
    let s = startRunner(compileWorkout(getWorkout('swing-emom')!, plan), 0);
    s = run(s, { type: 'done', now: 25_000 }, { type: 'done', now: 26_000 });
    expect(s.entries).toHaveLength(1);
    s = run(s, { type: 'tick', now: 60_000 });
    expect(s.index).toBe(1);
    s = run(s, { type: 'tick', now: 120_000 });
    expect(s.entries.map((e) => e.done)).toEqual([15, 15]);
    s = run(s, { type: 'skip', now: 130_000 });
    expect(s.entries.at(-1)?.done).toBe(0);
  });

  it('AMRAP logs rounds × reps per station', () => {
    let s = startRunner(compileWorkout(getWorkout('amrap-12')!, plan), 0);
    s = run(s, { type: 'round' }, { type: 'round' }, { type: 'round' }, { type: 'tick', now: 720_000 });
    expect(s.finished).toBe(true);
    expect(s.amrapRounds[0]).toBe(3);
    expect(s.entries.map((e) => e.done)).toEqual([30, 30, 18]);
  });
});
