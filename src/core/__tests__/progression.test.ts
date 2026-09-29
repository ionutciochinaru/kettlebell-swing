import { defaultLoad, progressByEffort, progressSets, type Prescription } from '../progression';

const bells = [8, 12, 16, 20, 24];
const at = (load: number, reps: number, extra: Partial<Prescription> = {}): Prescription => ({
  load,
  reps,
  missStreak: 0,
  easyStreak: 0,
  ...extra,
});

describe('progressSets (double progression)', () => {
  it('adds a rep when every set reaches the target', () => {
    const r = progressSets(at(16, 10), [10, 15], [10, 10, 11], 'good', bells);
    expect(r.change).toBe('reps-up');
    expect(r.next).toMatchObject({ load: 16, reps: 11 });
  });

  it('adds two reps when rated easy, capped at the top of the range', () => {
    expect(progressSets(at(16, 10), [10, 15], [10, 10], 'easy', bells).next.reps).toBe(12);
    expect(progressSets(at(16, 14), [10, 15], [14, 14], 'easy', bells).next.reps).toBe(15);
  });

  it('moves to the next bell and resets reps when every set hits the top', () => {
    const r = progressSets(at(16, 15), [10, 15], [15, 15, 15], 'good', bells);
    expect(r.change).toBe('load-up');
    expect(r.next).toMatchObject({ load: 20, reps: 10 });
  });

  it('holds when rated hard even if the top was reached', () => {
    const r = progressSets(at(16, 15), [10, 15], [15, 15], 'hard', bells);
    expect(r.change).toBe('hold');
    expect(r.next.load).toBe(16);
  });

  it('reports maxed with the heaviest bell', () => {
    expect(progressSets(at(24, 15), [10, 15], [15, 15], 'good', bells).change).toBe('maxed');
  });

  it('holds after one miss and deloads after two consecutive misses', () => {
    const first = progressSets(at(20, 10), [10, 15], [10, 8], 'hard', bells);
    expect(first.change).toBe('hold');
    expect(first.next.missStreak).toBe(1);
    const second = progressSets(first.next, [10, 15], [9, 7], 'hard', bells);
    expect(second.change).toBe('load-down');
    expect(second.next).toMatchObject({ load: 16, reps: 10, missStreak: 0 });
  });

  it('clamps an out-of-range stored target into the block range', () => {
    const r = progressSets(at(16, 3), [8, 12], [8, 8], 'good', bells);
    expect(r.next.reps).toBe(9);
  });
});

describe('progressByEffort', () => {
  it('needs two consecutive easy sessions to add load', () => {
    const one = progressByEffort(at(16, 10), 'easy', bells);
    expect(one.next.load).toBe(16);
    const two = progressByEffort(one.next, 'easy', bells);
    expect(two).toMatchObject({ change: 'load-up', next: { load: 20, easyStreak: 0 } });
  });

  it('hard resets the easy streak', () => {
    expect(progressByEffort(at(16, 10, { easyStreak: 1 }), 'hard', bells).next.easyStreak).toBe(0);
  });
});

describe('defaultLoad', () => {
  it('starts hinges mid-range and arms on the lightest bell', () => {
    expect(defaultLoad('kb-swing', bells)).toBe(16);
    expect(defaultLoad('kb-curl', bells)).toBe(8);
  });
});
