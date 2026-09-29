# Independent review and revision

Review the exported animation that the user will see. A contact sheet identifies pose defects; it cannot establish timing, smoothness or loop continuity. Use both a native-size full-cycle player and an enlarged labelled contact sheet, plus geometry evidence. Record any method that could not be exercised.

## Three roles

Give reviewers the exercise name, variant and counting convention, exact exported revision, ordered frames/timing, intended display size, source index, and their role. Do not give them the desired score, other initial scores, or an instruction to approve. Separate initial assessment from collaborative diagnosis.

| Reviewer | Scores | Must inspect |
| --- | --- | --- |
| Exercise form | Whether the visible sequence teaches the named exercise | Start/action/return, support and equipment use, exercise identity, alternate sides, variant consistency, source-supported cues. |
| Visuals | Whether the instruction reads clearly and feels deliberately drawn | Native-size silhouette, overlap, contact readability, contrast, stroke consistency, framing, pacing, loop and differentiation from similar exercises. |
| Anatomy/biomechanics | Whether the depicted body moves credibly | Constant world-space segments, joint articulation, knee/elbow bend direction, spine/pelvis relationships, foot/hand support, balance transitions, equipment attachment and depth projection. |

The anatomy reviewer should distinguish geometric impossibility from normal differences in proportions, mobility and technique. The form reviewer should not apply a clinical diagnosis to a drawing. All reviewers should identify confidence and remaining uncertainty. These are AI/editorial reviews informed by evidence, not professional certification.

## Score anchors

Use integers 1–10 for each exercise in each role. The examples calibrate judgment; they are not automatic scoring formulas.

| Score | Meaning |
| --- | --- |
| 1–2 | Contradictory or missing action, unreadable instruction, or severe impossible motion. |
| 3–4 | Exercise recognizable, but major defects would mislead a viewer. |
| 5–6 | Main action present; substantial ambiguity or repeated defects remain. |
| 7 | Generally convincing, with a meaningful unresolved correction. |
| 8 | Clear and credible reference for the represented variant; no unresolved major defect in this reviewer's scope. |
| 9 | Strong clarity and control through transitions, contact and native-size playback. |
| 10 | Exceptional reference with thoroughly demonstrated clarity; reserve for evidence that supports it. |

Do not convert a passing test suite into an 8. Do not increase a score merely because the implementer made a change. Reinspect actual revised assets. An attractive outline cannot offset an incorrect knee lift, and exact bone lengths cannot offset an unreadable silhouette.

## Review record

A compact JSON or table should retain:

```text
reviewer role and identity
revision identifier or exported-asset hash
exercise id and variant
score / 10 and confidence
evidence inspected: playback, native size, contact sheet, geometry
observed defect + frame/phase + consequence
required correction and unresolved limitations
acceptance status against agreed threshold
```

Keep prior records when the motion changes. Initial scores remain independent. Once they are recorded, reviewers can share objective observations and a prioritized correction list. The implementer should address shared underlying defects before polishing individual frames, then regenerate exports and request a new review of affected motions.

## Release decision

For an agreed target of 8, every exercise must score at least 8 from all three roles. A mean of 8 with an anatomy score of 5 is a failure. Geometry or playback defects can also block delivery despite high subjective scores. Mark the exact current revision approved only when the evidence agrees.

If a reviewer can inspect stills but cannot actually observe playback, that review is partial; state timing/loop review as unrun. If one exercise remains below threshold, provide its real status and next correction instead of claiming the complete library passed. Do not discard the exercise or replace requested content merely to improve the aggregate score without addressing product scope.
