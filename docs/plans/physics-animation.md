# Plan: IK rig and physics-driven kettlebell motion

**Status:** proposal, 2026-09-29. Baseline revision `54e441838d09` is being scored by three reviewer agents and the user (`/debug/animations`).

## Problem

The current motions are keyframed joint targets with smooth curves. Bone lengths are exact, but nothing in the pipeline knows about mass. As a result:

- **The bell looks weightless.** Its path is authored rather than produced by momentum and gravity, so it moves at cosine speed, doesn't float at the top of a swing, and doesn't accelerate into the backswing.
- **The body doesn't respond to the load.** The hips don't shift back to counterbalance the bell. The shoulders don't pack down, the trunk doesn't brace, and the knees don't absorb a clean.
- **Limbs pass through each other.** The old validator didn't check this. The new clearance check finds:
  - arms 9–11 cm inside the thighs in the swing and deadlift;
  - the bell 13 cm inside the thigh in the clean and snatch;
  - the get-up's support arm passing through its leg.
- **Hands and the bell are placeholders.** Each hand is a two-point capsule, and the bell is a rough lathe shape with a thin line for a handle.

## Approach

Physics runs **offline** in the Python pipeline, which stays deterministic, testable and small to export. The app keeps playing baked clips. Real-time physics on the phone would add CPU cost and nondeterminism, and it wouldn't improve the lesson being taught.

```
motion spec (lift type, stance, bell mass, tempo)
   → physics layer: bell rigid body + body response (COM balance, bracing, absorption)
   → full-body IK: contacts > grip > balance > collision > style, with joint limits
   → validator v2: geometry + collisions + balance + dynamics plausibility
   → export v2: joint positions + bone/hand/bell orientations (30 fps)
   → app: stick figure with hands and a real kettlebell, driven by the clip
```

## Milestones

### M0: Baseline (in progress)
- Three independent reviews (form, visuals, anatomy) of every exercise at revision `54e441838d09`, plus your 1–10 scores and notes from the review page.
- **Deliverable:** baseline scores. Every later revision is compared against these on the same page.
- **Agent results (2026-09-29):** no exercise reaches 8 from all three reviewers.

  | Lowest score across reviewers | Exercises |
  | --- | --- |
  | 7 | goblet squat, reverse lunge, side lunge, bent-over row, curl |
  | 6 | swing, side bend, halo |
  | 5 | deadlift, upright row, press |
  | 4 | clean, snatch |
  | 3 | get-up |

- **Shared defects, most important first:**
  1. The hinge backswing is shared by the swing, deadlift, clean and snatch. It is low and knee-heavy, and the arms and bell pass through the thighs; they should go between the knees and hike high.
  2. Get-up: it stands up on one foot with the centre of mass outside the base; the leg sweeps through the support arm; the elbow never reaches the floor.
  3. Press: the elbow flares with the forearm off vertical.
  4. Upright row: the bell and elbows drift forward.
  5. Side bend and curl: the loaded arm is held away from the side.
  6. The load never looks heavy.
  7. Hands and bell are placeholders.
- **User scores (2026-09-29):**
  - 8: bent-over row
  - 7: goblet squat, reverse lunge, upright row, curl, halo
  - 6: side lunge
  - 5: swing
  - 4: deadlift, clean, get-up
  - 3: side bend, snatch
  - 2: press
- **User notes:** "hands going in the legs (and arms)" (swing, deadlift, clean, press, snatch, get-up); the side bend's weight "feels like paper, not a 10 15 20 kg weight"; halo glitches when the bell is in front; get-up "very stiff"; upright-row hands bend unnaturally.
- **Gap the user found:** the evidence only measured clearance against the legs. Measured afterwards:
  - the press bell sits 15 cm inside its own upper arm;
  - the clean and snatch bell passes about 10 cm through its own forearm;
  - the snatch bell overlaps the head by 3.6 cm.

  Validator v2 must check the bell and hands against **every** body part (arms, torso, head), and the halo's 1 cm clearance needs a margin.
- Full records: `docs/animation-review/54e441838d09/review-*.json` (including `review-user.json`), with sheets and `geometry.json` alongside.

### M1: Rig v2 (Python)
- **Hierarchical skeleton with rotations,** not just positions:
  - pelvis, lumbar, thoracic, neck and head;
  - clavicle with scapular elevation and depression;
  - shoulder, elbow, wrist, and a hand bone with finger-curl and thumb channels;
  - hip, knee, ankle and toe.
- **Joint limits** per joint (e.g. knee 0–150°, elbow 0–150° with no hyperextension beyond 5°, wrist ±70° / ±30°).
- **Segment masses and centres of mass** from standard anthropometric tables (de Leva 1996), for a reference 75 kg body.
- **Full-body IK solver** (damped least squares). Tasks in priority order:
  1. Contacts: planted feet, hands on the floor, knees down. Exact, as today.
  2. Grip: every hand on the handle surface, with the correct hand orientation.
  3. Balance: the combined body + bell centre of mass stays over the base of support.
  4. Collision: capsule separation between arms and thighs/torso, and between the bell and the legs.
  5. Style: posture targets from the motion spec.
- **Tests:** joint limits never exceeded, contacts exact, IK convergence, and the existing geometry checks.

### M2: Physics layer
- **Bell as a rigid body:** mass from the lift spec (default 16 kg), realistic inertia, and a grip constraint.
- **Ballistic lifts** (swing, clean, snatch): model the arm and bell as a pendulum driven by hip extension.
  - A hip impulse at the bottom sends the bell up; gravity decelerates it into a float; it accelerates back down into the hike.
  - Timing comes from the simulation (fast at the bottom, slow at the top), not from a cosine curve.
  - Clean: the elbow pulls in, the bell rotates around the hand, and the landing in the rack is absorbed by a brief knee bend.
  - Snatch: the punch-through happens at the float, when the bell is weightless.
- **Grinding lifts** (deadlift, squat, press, row, curl, get-up):
  - Speed profiles come from load versus joint torque capacity, so the lift slows at its sticking point, with a controlled lowering.
  - Minimal-jerk transitions between positions.
- **Body response to load:**
  - The pelvis and trunk shift each frame so the combined centre of mass stays over the feet (hips back when the bell is out front, a slight lean back at the top of a swing).
  - Shoulders pack down under a hanging bell, and the free arm counterbalances in single-arm lifts.
  - Small anticipation before the hip drive; follow-through after the catch.
- **Optional feasibility check in MuJoCo:** replay each clip, compute joint torques and ground reaction forces by inverse dynamics, and flag frames where required torques or foot pressure are impossible.

### M3: Validator v2
Adds to today's checks:
- **Limb and bell collisions:** minimum clearance at least 0 between drawn capsules, except for contacts that are intended (for example the forearms brushing the inner thighs in the hike pass).
- **Balance:** the combined centre of mass stays inside the support polygon, with a margin.
- **Free flight:** during the float, the bell's acceleration matches gravity minus arm tension within tolerance.
- **Joint limits and smoothness:** joint limits hold; jerk is bounded; there are no velocity spikes except at intended impacts.

A failing check blocks export, just as solver errors do today.

### M4: Hands and kettlebell (can start in parallel with M1)
- **Hands:** a stylised mitten (palm block, thumb and finger block) with authored grip poses:
  - hook grip around the handle for swings and deadlifts;
  - neutral wrist in the rack;
  - stacked wrist and fist at lockout;
  - flat palm on the floor in the get-up;
  - both hands side by side on one handle, or on the horns for the goblet squat and halo.
  - Fingers wrap to the handle's radius, so the grip reads at phone size.
- **Kettlebell:**
  - a cast-iron shape with a sphere body, flat base and shoulders into the horns;
  - a round handle tube following a real window arc, sized from real bells (about 19 cm across for 8 kg, 26 cm for 24 kg);
  - the bell's orientation comes from the physics, so it tips and rotates as it should;
  - optional colour bands by weight, like competition bells;
  - soft floor contact shadows.
- The bell's size in the app follows the user's selected bell.

### M5: Export v2 and app runtime
- The clip format adds bone rotations (quaternions), hand pose channels and the bell's orientation. Positions stay for compatibility.
- `figure.ts` builds hands and the new bell and reads orientations. It keeps the watch figure's look.
- Playback cost stays low: sample, interpolate, set transforms. No physics on the device.

### M6: Migrate the library, then review again
- **Order:**
  1. Swing, deadlift, clean, snatch: the most weight-dependent moves, and they have the collisions.
  2. Goblet squat, press, rows, curl, side bend, halo, lunges.
  3. Get-up.
- After each batch: capture, run the three reviews and your review, fix, and review again.
- **Acceptance:** each exercise scores at least 8 from all three reviewers and from you, with validator v2 passing.

## Decisions needed

1. **Physics tooling:**
   - Option A (recommended): write the pendulum/rigid-body and balance solver in Python with numpy, and use MuJoCo only as the optional feasibility check.
   - Option B: MuJoCo from the start, tracking the motions with controllers. That's heavier to build and tune.
2. **Character:** keep the watch-style stick figure and add hands (recommended, and matches your earlier choice), or move to a skinned mannequin mesh.
3. **Kettlebell look:** black cast iron, or competition bells coloured by weight.
4. **Weight variants:** bake one reference weight and only scale the bell's size, or bake light and heavy versions so a 24 kg swing visibly moves differently from an 8 kg one.

## Risks

- **IK solver tuning:** full-body IK with priorities and collisions takes tuning. Mitigation: port one lift (the swing) end to end first.
- **Look drift:** more realistic motion may move away from the watch figure's look. The renderer style stays the same; only motion, hands and bell change.
- **Review limits:** reviewers only see stills. The review page is where timing and weight get judged, so your scores carry the playback judgement.
