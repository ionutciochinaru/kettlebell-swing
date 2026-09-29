/**
 * Progressive overload.
 *
 * Strength sets use double progression inside a rep range: add reps until every
 * set reaches the top of the range, then move to the next heavier bell you own
 * and restart at the bottom. Two sessions in a row below the range step back
 * down. Timed and circuit work progress load from effort ratings instead:
 * two Easy ratings in a row move to the next bell.
 */
import { getExercise, type Pattern } from './exercises';

export type Effort = 'easy' | 'good' | 'hard';

export type Prescription = {
  load: number;
  /** Next target reps for strength sets. */
  reps: number;
  missStreak: number;
  easyStreak: number;
};

export type Change = 'load-up' | 'load-down' | 'reps-up' | 'hold' | 'maxed';

export type Progress = { next: Prescription; change: Change; reason: string };

export function sortedBells(bells: number[]): number[] {
  return [...new Set(bells)].filter((b) => b > 0).sort((a, b) => a - b);
}

export function heavierBell(load: number, bells: number[]): number | undefined {
  return sortedBells(bells).find((b) => b > load);
}

export function lighterBell(load: number, bells: number[]): number | undefined {
  return sortedBells(bells).reverse().find((b) => b < load);
}

const START_FRACTION: Record<Pattern, number> = {
  hinge: 0.5,
  squat: 0.34,
  lunge: 0.2,
  pull: 0.2,
  arms: 0,
  core: 0,
};

/** Conservative starting bell: hinges start mid-range, small muscles lightest. */
export function defaultLoad(exerciseId: string, bells: number[]): number {
  const sorted = sortedBells(bells);
  if (!sorted.length) return 0;
  const fraction = START_FRACTION[getExercise(exerciseId).pattern];
  return sorted[Math.floor((sorted.length - 1) * fraction)];
}

export function initialPrescription(exerciseId: string, bells: number[], repMin = 8): Prescription {
  return { load: defaultLoad(exerciseId, bells), reps: repMin, missStreak: 0, easyStreak: 0 };
}

/** Clamp a stored target into a block's rep range. */
export function targetReps(prev: Prescription, repRange: [number, number]): number {
  return Math.min(repRange[1], Math.max(repRange[0], prev.reps));
}

export function progressSets(
  prev: Prescription,
  repRange: [number, number],
  setReps: number[],
  effort: Effort | undefined,
  bells: number[],
): Progress {
  const [min, max] = repRange;
  const target = targetReps(prev, repRange);
  const base = { ...prev, reps: target, easyStreak: 0 };
  if (!setReps.length) return { next: base, change: 'hold', reason: 'No sets completed.' };

  if (setReps.some((r) => r < min)) {
    const missStreak = prev.missStreak + 1;
    const lighter = lighterBell(prev.load, bells);
    if (missStreak >= 2 && lighter !== undefined) {
      return {
        next: { ...base, load: lighter, reps: min, missStreak: 0 },
        change: 'load-down',
        reason: `Below ${min} reps two sessions running. Dropping to ${lighter} kg to rebuild.`,
      };
    }
    return {
      next: { ...base, missStreak },
      change: 'hold',
      reason: `A set fell below ${min} reps. Same target next time.`,
    };
  }

  if (effort === 'hard') {
    return { next: { ...base, missStreak: 0 }, change: 'hold', reason: 'Rated hard. Repeat this target.' };
  }

  if (setReps.every((r) => r >= max)) {
    const heavier = heavierBell(prev.load, bells);
    if (heavier === undefined) {
      return {
        next: { ...base, reps: max, missStreak: 0 },
        change: 'maxed',
        reason: `Top of the range with your heaviest bell. Add a set, slow the tempo or get a heavier bell.`,
      };
    }
    return {
      next: { ...base, load: heavier, reps: min, missStreak: 0 },
      change: 'load-up',
      reason: `Every set hit ${max}. Move up to ${heavier} kg at ${min} reps.`,
    };
  }

  const reached = setReps.every((r) => r >= target);
  if (!reached) {
    return { next: { ...base, missStreak: 0 }, change: 'hold', reason: `Aim for ${target} on every set again.` };
  }
  const step = effort === 'easy' ? 2 : 1;
  const reps = Math.min(max, target + step);
  return {
    next: { ...base, reps, missStreak: 0 },
    change: 'reps-up',
    reason: `All sets reached ${target}. Next target ${reps} reps.`,
  };
}

/** Circuits, intervals, EMOM, AMRAP and ladders: load follows effort. */
export function progressByEffort(prev: Prescription, effort: Effort | undefined, bells: number[]): Progress {
  if (effort === 'easy') {
    const easyStreak = prev.easyStreak + 1;
    const heavier = heavierBell(prev.load, bells);
    if (easyStreak >= 2 && heavier !== undefined) {
      return {
        next: { ...prev, load: heavier, easyStreak: 0 },
        change: 'load-up',
        reason: `Easy twice in a row. Next time use ${heavier} kg.`,
      };
    }
    return { next: { ...prev, easyStreak }, change: 'hold', reason: 'Easy. One more easy session moves you up a bell.' };
  }
  if (effort === 'hard') {
    return { next: { ...prev, easyStreak: 0 }, change: 'hold', reason: 'Hard. Stay at this bell.' };
  }
  return { next: prev, change: 'hold', reason: 'Good. Keep this bell.' };
}
