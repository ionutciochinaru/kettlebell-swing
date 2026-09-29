"""Capsule collision model matching the drawn 3D figure (src/animation/figure.ts).

Clearance < 0 means two drawn parts interpenetrate. Every body part is checked
against the bell and the hands/forearms; intended contacts are allowlisted per
motion with a small tolerance (e.g. a racked bell resting on the forearm).
"""
from math import sqrt

# name: (joint a, joint b, radius)
PARTS = {
    'head': ('head', 'head', .10),
    'torso': ('pelvis', 'chest', .085),
    **{f'{name}_{s}': (f'{a}_{s}', f'{b}_{s}', r) for s in 'lr' for name, a, b, r in [
        ('upper_arm', 'shoulder', 'elbow', .055),
        ('forearm', 'elbow', 'wrist', .027),
        ('hand', 'wrist', 'palm', .04),
        ('thigh', 'hip', 'knee', .073),
        ('shin', 'knee', 'ankle', .047),
    ]},
}

PAIRS = [
    *[(f'{arm}_{s}', f'{leg}_{t}') for s in 'lr' for t in 'lr'
      for arm in ('upper_arm', 'forearm', 'hand') for leg in ('thigh', 'shin')],
    *[(f'{arm}_{s}', part) for s in 'lr' for arm in ('forearm', 'hand') for part in ('head', 'torso')],
    ('thigh_l', 'thigh_r'), ('shin_l', 'shin_r'), ('shin_l', 'thigh_r'), ('shin_r', 'thigh_l'),
    ('forearm_l', 'forearm_r'), ('upper_arm_l', 'head'), ('upper_arm_r', 'head'),
]
BELL_TARGETS = ['head', 'torso', *[f'{p}_{s}' for s in 'lr' for p in
                                  ('upper_arm', 'forearm', 'hand', 'thigh', 'shin')]]


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def segment_distance(p1, q1, p2, q2):
    """Closest distance between segments p1q1 and p2q2 (Ericson, RTCD 5.1.9)."""
    d1, d2, r = _sub(q1, p1), _sub(q2, p2), _sub(p1, p2)
    a, e, f = _dot(d1, d1), _dot(d2, d2), _dot(d2, r)
    eps = 1e-12
    if a <= eps and e <= eps:
        return sqrt(_dot(r, r))
    if a <= eps:
        s, t = 0., min(1., max(0., f / e))
    else:
        c = _dot(d1, r)
        if e <= eps:
            t, s = 0., min(1., max(0., -c / a))
        else:
            b = _dot(d1, d2)
            denom = a * e - b * b
            s = min(1., max(0., (b * f - c * e) / denom)) if denom > eps else 0.
            t = (b * s + f) / e
            if t < 0:
                t, s = 0., min(1., max(0., -c / a))
            elif t > 1:
                t, s = 1., min(1., max(0., (b - c) / a))
    c1 = tuple(p + d * s for p, d in zip(p1, d1))
    c2 = tuple(p + d * t for p, d in zip(p2, d2))
    return sqrt(_dot(_sub(c1, c2), _sub(c1, c2)))


def _capsule(pose, name):
    a, b, r = PARTS[name]
    j = pose['joints']
    return j[a], j[b], r


def clearances(pose):
    """{pair: clearance_m} for body pairs and bell (sphere + handle) vs body parts."""
    out = {}
    for x, y in PAIRS:
        (a0, a1, ra), (b0, b1, rb) = _capsule(pose, x), _capsule(pose, y)
        out[f'{x}|{y}'] = segment_distance(a0, a1, b0, b1) - ra - rb
    for i, prop in enumerate(pose['props']):
        if prop.get('type') != 'kettlebell':
            continue
        c, r = prop['center'], prop['radius']
        for target in BELL_TARGETS:
            p0, p1, rt = _capsule(pose, target)
            out[f'bell{i}|{target}'] = segment_distance(c, c, p0, p1) - r * .98 - rt
    return out


def worst(poses, allow=None):
    """Worst clearance per pair over a clip, minus allowlisted tolerance."""
    allow = allow or {}
    result = {}
    for k, pose in enumerate(poses):
        for pair, value in clearances(pose).items():
            tolerance = next((tol for pattern, tol in allow.items() if pattern in pair), 0.)
            adjusted = value + tolerance
            if pair not in result or adjusted < result[pair][0]:
                result[pair] = (adjusted, k / len(poses), value)
    return result
