import { BLOCK_KINDS, defaultBlock, describeWorkout, emptyWorkout, moveItem, normalizeBlock, validateWorkout } from '../builder';
import { compileWorkout, estimateSeconds } from '../timeline';

describe('builder', () => {
  it('every default block compiles into a runnable timeline', () => {
    for (const kind of BLOCK_KINDS) {
      const workout = { id: 'w', name: 'w', summary: '', blocks: [defaultBlock(kind, 'kb-clean')] };
      expect(validateWorkout(workout)).toEqual([]);
      expect(compileWorkout(workout, { load: () => 16, reps: (_, [min]) => min }).length).toBeGreaterThan(0);
    }
  });

  it('requires a name, blocks and exercises', () => {
    const w = emptyWorkout();
    expect(validateWorkout(w)).toContain('Give the workout a name.');
    expect(validateWorkout({ ...w, name: 'x', blocks: [] })).toContain('Add at least one block.');
    expect(validateWorkout({ ...w, name: 'x', blocks: [{ kind: 'amrap', minutes: 5, stations: [] }] })[0]).toMatch(/add an exercise/);
  });

  it('keeps interval station targets equal to the work time', () => {
    const block = normalizeBlock({ ...defaultBlock('intervals'), work: 45 } as ReturnType<typeof defaultBlock>);
    expect(block.kind === 'intervals' && block.stations[0].target).toEqual({ seconds: 45 });
  });

  it('describes and reorders', () => {
    const w = { id: 'w', name: 'w', summary: '', blocks: [defaultBlock('sets', 'kb-press'), defaultBlock('emom', 'kb-snatch')] };
    expect(describeWorkout(w)).toBe('Strength sets + EMOM: Single-arm press, Single-arm snatch.');
    expect(moveItem([1, 2, 3], 2, 0)).toEqual([3, 1, 2]);
    expect(moveItem([1, 2, 3], 0, -1)).toEqual([1, 2, 3]);
  });

  it('estimates a get-up rep much longer than a swing rep', () => {
    const plan = { load: () => 16, reps: (_: string, [min]: [number, number]) => min };
    const getups = compileWorkout({ id: 'g', name: 'g', summary: '', blocks: [{ kind: 'ladder', exercise: 'kb-getup', from: 1, to: 1, step: 1, rest: 0 }] }, plan);
    expect(estimateSeconds(getups)).toBe(60);
  });
});
