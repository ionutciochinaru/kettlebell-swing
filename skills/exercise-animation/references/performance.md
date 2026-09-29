# Performance and evidence

Optimize the exported product, not merely the authoring tool. A more capable offline rig can yield the same small 2D frame format and no added runtime math.

## Set explicit budgets

Record target display dimensions, frame dimensions, alpha/color format, number of frames, timing, package-size budget and playback method. Choose values from project needs and actual platform constraints. For a small watch demonstration, these are candidate starting profiles—not platform facts or universal limits:

| Motion | Candidate export | Loop duration |
| --- | --- | --- |
| Simple bilateral rep | 24 frames at 8 fps | 3 seconds |
| Rep with more visible transitions | 32 frames at 8 fps | 4 seconds |
| Alternating sequence needing clear resets | 32 frames at 6 fps | About 5.3 seconds |
| Plank or other steady hold | One static pose | No repeated frame decoding needed |

Longer phases or variable frame durations may improve teaching. If the platform does not support per-frame timing, encode deliberate holds consistently with its supported playback contract. Read current official documentation before using an unfamiliar API; a skill's notes do not prove runtime support.

A watch should not need to calculate inverse kinematics, load a human mesh, stream a clip or contact a remote API to display a pre-rendered stick figure. Prefer the existing local asset/playback system when it meets the task. Libraries belong in the authoring pipeline only when their concrete benefit outweighs added setup and maintenance.

## Three different resource measurements

Report these separately:

1. **Source bytes:** measured PNG/WebP/etc. file sizes and packaged size. Compression reduces these bytes but does not by itself reduce decoded dimensions.
2. **Decoded-frame estimate:** width × height × bytes per pixel × simultaneously resident frames, with assumptions stated. For example, a 280 × 156 RGBA image is 174,720 bytes (about 171 KiB) before decoder/cache/allocator overhead. All 32 such images would be about 5.33 MiB if resident at once. That is an estimate, not measured app RAM.
3. **Actual runtime measurements:** measured memory, decode latency, dropped frames, responsiveness and battery behavior on the target device. Device/firmware, test duration and procedure must accompany claims. Build or simulator success does not establish these results.

If cache residency is unknown, say so. Avoid promising that only one frame is resident merely because the app displays one image widget. Hardware evidence is needed for reliable memory/battery conclusions.

## Authoring and runtime checks

- Verify the output manifest matches asset names, dimensions, frame counts and durations. Keep evidence tied to the exact export revision.
- Inspect all poses for clipping at the largest extent; account for the real image viewport and any round-screen mask. Do not resize the figure dynamically to hide clipping.
- Check contact and grip positions, segment lengths and cycle boundaries in the motion data. World-space invariants and projected-image bounds are different checks.
- Use the real playback sequence at native size to inspect speed, turnarounds, side changes and the final-to-first transition. A GIF in a document or a static contact sheet is insufficient evidence unless it was actually played.
- When changing product playback, preserve lifecycle cleanup: cancel the prior animation on navigation/destruction and avoid duplicate playback work. Verify behavior using the project's documented platform contract.
- Keep an unmodified baseline and export each revision's review sheets/player separately. Reusing a file path is not evidence that a reviewer saw the new bytes.

Once relevant checks pass, retest only where a later edit or unresolved concern warrants it. Report exactly which host checks, rendered playback, simulator checks and hardware measurements ran.
