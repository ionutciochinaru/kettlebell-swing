---
name: exercise-animation
description: Create, repair, and review instructional exercise animations, especially simple stick figures exported as compact offline frames for small screens. Use when the motion must teach recognizable exercise form, with credible anatomy and clear visual presentation.
---

# Exercise Animation

Produce a reference a person can follow. Movement correctness, small-screen legibility, and runtime cost are separate acceptance criteria.

Preserve the user's chosen style and platform. For simple stick figures, refine pose, stroke, spacing and motion; do not substitute realistic human meshes or a large game engine. A constrained skeleton calculated offline can project to clean 2D artwork. It does not require the product to run a 3D rig, fetch media, or add a network dependency.

## Establish the motion before rendering

Inspect existing exercise definitions, assets, animation timing, target dimensions and generator before changing them. Preserve a baseline of the actual exported frames and timing. Do not judge source code alone or overwrite comparison evidence.

For each exercise, write a short motion contract: named variant, start pose, action phases, return, contacts, camera, timing, side alternation, and equipment grip. Open relevant primary instruction sources. [Form contracts](references/form-contracts.md) indexes useful sources and reference questions; it is not a substitute for reading the current page. Distinguish source facts from production choices. Avoid universal joint-angle or depth rules and do not imply professional certification.

Resolve instruction mismatches explicitly. A loop labelled “alternate” must show both sides; an isometric hold must not resemble repetitions. A comfortable shallow squat is a valid variant. A leg pointing backward cannot represent a forward knee lift merely because it shares the same title.

## Build contact-driven motion

Use fixed-length skeletal segments and articulated joints. Animate joint rotations, root motion and explicit contact phases; solve connected joints with forward or inverse kinematics as appropriate. Do not independently interpolate every screen-space joint coordinate: the limbs will shorten, grow, detach, or pass through the floor.

For planted hands, feet, knees, chair contacts or held equipment, constrain the correct endpoints in world coordinates. Swinging feet need clearance, followed by deliberate landing and weight transfer. A calf raise rotates about the forefoot; a reverse lunge keeps the front foot planted. A dumbbell follows the hand; both kettlebell hands share the handle. Contact constraints are checked through the entire cycle, not only at two keyframes.

For movement in depth, an offline 3D skeleton with fixed camera projection is often simpler to validate than improvised 2D foreshortening. A 2D rig is also suitable when its view makes the motion clear. Use an existing reliable library if it improves the result without unnecessary dependencies. In a repository that already has rig, motion, rendering and export modules, extend their ownership boundaries instead of creating a parallel generator.

Choose a stable camera for the teaching task: side or three-quarter views for hinges and presses, front or three-quarter for lateral steps and bilateral arm opening. Keep left/right identity, contact points, limb overlap and equipment visible. Frame the largest pose without changing scale every frame. Author neutral, reversal and return phases deliberately; repeating a cosine morph is not a motion plan.

## Render simply, then inspect

Stick figures still need readable shoulders, hips, elbows, knees, hands and feet. Use consistent proportions, rounded antialiased strokes, controlled near/far contrast and enough negative space to distinguish limbs. Avoid decorative details that obscure contact or exhaust a small display's pixels.

Export the real product assets and a review player using the same ordered frames and durations. Provide both full-cycle playback and labelled contact sheets. Review at native display size as well as enlarged size. Rebuild review artifacts after each revision so judges never score stale exports. Read [Performance and evidence](references/performance.md) when choosing frame budgets, playback behavior or reporting resource use.

Keep the variant, counting convention and phase/contact summary beside each exported clip. Record hashes at review start and verify them again at completion; a mutable folder name is not a revision identity. Drive a review player's frame index from elapsed time so display refresh rounding does not silently change the declared playback rate.

Geometry checks should cover fixed segment lengths, contact drift, floor penetration, grip attachment, side sequencing, bounds and loop continuity. Use appropriate tolerances for the rig and projection. Passing these checks does not establish that the exercise looks right.

## Three independent reviewers

For a full creation or substantive repair, use the requested team of three reviewers: exercise form, visuals, and anatomy/biomechanics. Give each the same raw exports and intended exercise, with their own scope from [Review rubric](references/review-rubric.md). Initial scores must be independent. After that, share objective defects, revise, and have each reviewer inspect the changed exports. If only two reviewer slots are available, run the third after one finishes; do not count the implementer's opinion as three independent agents.

Each reviewer scores every relevant exercise from 1–10, cites observed frames or phases, states confidence and lists unresolved defects. Treat 8/10 in every dimension as a useful project acceptance target unless the user specifies another. Never average away a failure or instruct a reviewer to award a minimum score. Do not report “all three passed” without three recorded reviews of the current exported revision. If a requested reviewer or playback method is unavailable, record that gap instead of inventing review evidence.

Make focused corrections supported by review findings. Stop broad rework when the agreed checks pass; if an item remains below threshold, show its remaining defect and actual status. Preserve baseline and subsequent scores. The score is an editorial judgment, not a safety certification.

## Deliver

Provide the working assets and generator changes, compact source/variant records, review artifacts and scores, checks actually run, and any runtime validation gaps. Separate rendered-preview success from simulator and hardware results. Do not imply an animation's source PNG size establishes actual RAM use, battery cost or playback smoothness.
