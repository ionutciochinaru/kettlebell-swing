/**
 * Session runner state machine. Pure: time is passed in, so the UI ticks it
 * and tests drive it deterministically. Pausing shifts the step start.
 */
import type { SetEntry } from './session';
import type { Step } from './timeline';

export type RunnerState = {
  steps: Step[];
  index: number;
  stepStart: number;
  pausedAt?: number;
  entries: SetEntry[];
  amrapRounds: Record<number, number>;
  /** Reps awaiting confirmation after Done on a rep set. */
  review?: number;
  /** EMOM minute already logged; the window keeps running as rest. */
  windowLogged: boolean;
  restExtra: number;
  finished: boolean;
};

export type RunnerAction =
  | { type: 'tick'; now: number }
  | { type: 'done'; now: number }
  | { type: 'adjust'; delta: number }
  | { type: 'confirm'; now: number }
  | { type: 'skip'; now: number }
  | { type: 'round' }
  | { type: 'extendRest'; seconds: number }
  | { type: 'pause'; now: number }
  | { type: 'resume'; now: number }
  | { type: 'finish' };

export function startRunner(steps: Step[], now: number): RunnerState {
  return { steps, index: 0, stepStart: now, entries: [], amrapRounds: {}, windowLogged: false, restExtra: 0, finished: steps.length === 0 };
}

export function currentStep(state: RunnerState): Step | undefined {
  return state.steps[state.index];
}

export function elapsed(state: RunnerState, now: number): number {
  return Math.max(0, ((state.pausedAt ?? now) - state.stepStart) / 1000);
}

/** Countdown length of the current step, or undefined for open-ended rep sets. */
export function stepDuration(state: RunnerState): number | undefined {
  const step = currentStep(state);
  if (!step) return undefined;
  if (step.kind === 'rest') return step.duration + state.restExtra;
  if (step.kind === 'amrap') return step.duration;
  return step.duration;
}

export function remaining(state: RunnerState, now: number): number | undefined {
  const duration = stepDuration(state);
  return duration === undefined ? undefined : Math.max(0, duration - elapsed(state, now));
}

function log(state: RunnerState, done: number): RunnerState {
  const step = currentStep(state);
  if (!step || step.kind !== 'work') return state;
  const entry: SetEntry = {
    exercise: step.exercise,
    blockKind: step.blockKind,
    block: step.block,
    load: step.load,
    target: step.target,
    done,
  };
  return { ...state, entries: [...state.entries, entry] };
}

function logAmrap(state: RunnerState): RunnerState {
  const step = currentStep(state);
  if (!step || step.kind !== 'amrap') return state;
  const rounds = state.amrapRounds[step.block] ?? 0;
  const entries: SetEntry[] = step.stations.map((s) => ({
    exercise: s.exercise,
    blockKind: 'amrap',
    block: step.block,
    load: s.load,
    target: s.target,
    done: rounds * ('reps' in s.target ? s.target.reps : s.target.seconds),
  }));
  return { ...state, entries: [...state.entries, ...(rounds ? entries : [])] };
}

function advance(state: RunnerState, now: number): RunnerState {
  const index = state.index + 1;
  return {
    ...state,
    index,
    stepStart: now,
    pausedAt: state.pausedAt === undefined ? undefined : now,
    review: undefined,
    windowLogged: false,
    restExtra: 0,
    finished: index >= state.steps.length,
  };
}

export function runnerReducer(state: RunnerState, action: RunnerAction): RunnerState {
  const step = currentStep(state);
  if (action.type === 'finish') return { ...state, finished: true };
  if (state.finished || !step) return state;

  switch (action.type) {
    case 'tick': {
      if (state.pausedAt !== undefined) return state;
      const left = remaining(state, action.now);
      if (left === undefined || left > 0) return state;
      if (step.kind === 'rest') return advance(state, action.now);
      if (step.kind === 'amrap') return advance(logAmrap(state), action.now);
      if (step.mode === 'timed') return advance(log(state, step.duration ?? 0), action.now);
      if (step.mode === 'window') {
        // An unlogged EMOM minute counts as completed at target; use Missed to record otherwise.
        const logged = state.windowLogged ? state : log(state, 'reps' in step.target ? step.target.reps : 0);
        return advance(logged, action.now);
      }
      return state;
    }
    case 'done': {
      if (step.kind !== 'work') return state;
      if (step.mode === 'reps') return { ...state, review: 'reps' in step.target ? step.target.reps : 0 };
      if (step.mode === 'window') {
        if (state.windowLogged) return state;
        return { ...log(state, 'reps' in step.target ? step.target.reps : 0), windowLogged: true };
      }
      return advance(log(state, Math.round(elapsed(state, action.now))), action.now);
    }
    case 'adjust':
      return state.review === undefined ? state : { ...state, review: Math.max(0, state.review + action.delta) };
    case 'confirm':
      return state.review === undefined ? state : advance(log(state, state.review), action.now);
    case 'skip':
      if (step.kind === 'amrap') return advance(logAmrap(state), action.now);
      if (step.kind === 'work' && step.mode === 'window' && !state.windowLogged) {
        // Missed minute: record zero so progression sees it.
        return advance(log(state, 0), action.now);
      }
      return advance(state, action.now);
    case 'round':
      if (step.kind !== 'amrap') return state;
      return { ...state, amrapRounds: { ...state.amrapRounds, [step.block]: (state.amrapRounds[step.block] ?? 0) + 1 } };
    case 'extendRest':
      return step.kind === 'rest' ? { ...state, restExtra: state.restExtra + action.seconds } : state;
    case 'pause':
      return state.pausedAt === undefined ? { ...state, pausedAt: action.now } : state;
    case 'resume':
      return state.pausedAt === undefined
        ? state
        : { ...state, stepStart: state.stepStart + (action.now - state.pausedAt), pausedAt: undefined };
  }
  return state;
}
