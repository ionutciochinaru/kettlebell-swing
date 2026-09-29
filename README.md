# Kettlebell Swing

A kettlebell training app for iOS, Android and web, built with Expo. It runs circuits, EMOMs, AMRAPs, intervals, ladders and strength sets, tracks every set, and applies progressive overload using the bells you own. Each exercise is demonstrated by a looping 3D figure you can drag to inspect the form from any angle.

## Features

- **Training types:** strength sets (double progression), circuits, EMOM, AMRAP, intervals/Tabata, ladders. Workouts are lists of blocks, compiled into a step timeline (`src/core/timeline.ts`).
- **Progressive overload** (`src/core/progression.ts`)
  - **Strength sets:** add reps within the rep range; when every set hits the top, move to your next heavier bell. Two sessions in a row below the range step back down.
  - **Timed and circuit work:** two Easy ratings in a row move you up a bell.
- **Session runner** (`src/core/runner.ts`, `src/app/session.tsx`)
  - Rep sets: Done, then confirm the reps you actually did.
  - Countdowns for timed work, rest, EMOM minutes and AMRAPs.
  - Pause, +15 s rest, haptic cues and keep-awake.
- **3D demonstrations:** the figure from the Spamset watch app, rendered live with three.js. It uses the same proportions, tapered limbs, orange shirt, trousers, shoes and kettlebell. The side nearer the camera is drawn in ivory, as on the watch.
- **Accounts:** Google, Apple, or offline. Data is local-first (SQLite-backed storage on device) and syncs to Supabase when you sign in.

## Develop

```sh
npm install
npx expo start          # press w for web; use a development build for iOS/Android
npm test                # jest: progression, timelines, runner
npm run typecheck
npx expo lint
```

Expo Go does not include every native module this app uses (GL, Apple sign-in). Build a development client with `npx expo run:ios|android` or `eas build --profile development`.

## Accounts (optional)

Without Supabase keys the app runs offline-only. To enable sign-in:

1. Create a Supabase project, or run `eas integrations:supabase:connect`.
2. Copy `.env.example` to `.env.local` and fill in `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
3. Apply `supabase/migrations/0001_init.sql`. It creates the tables with row-level security.
4. In Supabase Auth, enable the Google and Apple providers. Add redirect URLs: `kettlebellswing://auth-callback` and your web origin.

On iOS, Apple sign-in is native; on Android and web it uses browser OAuth. Google uses browser OAuth everywhere.

## Animation pipeline

`tools/animation/` is the rig from the Spamset watch app: a fixed-length 3D stick skeleton, contact-driven motions, kettlebell choreography, a geometry validator and the PNG renderer.

```sh
npm run animations            # export 3D joint tracks + list thumbnails
npm run validate:animations   # geometry checks (segment lengths, contacts, loops)
```

- `export_3d.py` samples each motion at 30 fps into `assets/animations/*.json` (joint positions in mm) and regenerates `src/animation/clips.ts`. The export fails on any IK error.
- `export_thumbs.py` draws list thumbnails with the unchanged watch renderer.
- `src/animation/figure.ts` builds the 3D figure from those joints.

To add an exercise, author its motion in `tools/animation/` following `skills/exercise-animation/SKILL.md`. Then add it to `EXERCISES` in `export_3d.py` and `src/core/exercises.ts`, and run `npm run animations`.
