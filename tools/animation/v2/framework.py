"""Keyed lifts with load-aware balance.

A Lift is authored as key states (phase -> parameters). Between keys the state
follows a minimum-jerk profile (grinds: stop, then move smoothly) or a periodic
Hermite spline (flowing lifts). A build function turns a state into a pose,
applying a hip shift (dx, dy) to the pelvis only; feet and floor contacts stay
put, and everything carried by the trunk moves with it.

Balance: over the whole loop we solve the smooth, periodic hip shift that keeps
the zero-moment point (ZMP) of body + bell at the centre of the current support
area (cart-table model). With a 16 kg bell this produces the counter-lean and
hip shift a lifter makes to carry the load, and it anticipates support changes
(e.g. shifting over the front foot before the rear foot leaves the floor).
"""
from functools import cached_property

try:
    from .body import centre_of_mass, support_points, convex_hull, margin, G
    from .swing import solve_cyclic
except ImportError:
    from v2.body import centre_of_mass, support_points, convex_hull, margin, G
    from v2.swing import solve_cyclic

SAMPLES_PER_SECOND = 240


def minjerk(u):
    u = min(1., max(0., u))
    return u * u * u * (10 - 15 * u + 6 * u * u)


def _lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


def _hermite_scalar(keys, phase, param):
    """Periodic non-uniform Catmull-Rom on one parameter; 'hold' keys have zero slope."""
    n = len(keys)
    times = [k[0] for k in keys]

    def value(i):
        return keys[i % n][1][param]

    def time(i):
        return times[i % n] + (i // n)

    def slope(i):
        if keys[i % n][2]:
            return 0.
        return (value(i + 1) - value(i - 1)) / (time(i + 1) - time(i - 1))

    i = max((k for k in range(n) if times[k] <= phase), default=-1)
    t0, t1 = (time(i), time(i + 1)) if i >= 0 else (times[-1] - 1, times[0])
    h = t1 - t0
    u = (phase - t0) / h
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    return h00 * value(i) + h10 * h * slope(i) + h01 * value(i + 1) + h11 * h * slope(i + 1)


SAFE_MARGIN = .06


def _safe_target(pose, com):
    """Where the balance point should be: the COM itself if it is at least SAFE_MARGIN
    inside the support, otherwise the nearest point toward the support centre that is."""
    hull = convex_hull(support_points(pose))
    centre = _support_centre(pose)
    if not hull or centre is None:
        return com
    point = (com[0], com[1])
    if margin(point, hull) >= SAFE_MARGIN:
        return point
    lo, hi = 0., 1.
    if margin(centre, hull) < SAFE_MARGIN:
        return centre
    for _ in range(30):
        mid = (lo + hi) / 2
        q = (point[0] + (centre[0] - point[0]) * mid, point[1] + (centre[1] - point[1]) * mid)
        lo, hi = (lo, mid) if margin(q, hull) >= SAFE_MARGIN else (mid, hi)
    return (point[0] + (centre[0] - point[0]) * hi, point[1] + (centre[1] - point[1]) * hi)


def _support_centre(pose):
    hull = convex_hull(support_points(pose))
    if not hull:
        return None
    area = cx = cy = 0.
    for (x0, y0), (x1, y1) in zip(hull, hull[1:] + hull[:1]):
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(area) < 1e-9:
        return sum(p[0] for p in hull) / len(hull), sum(p[1] for p in hull) / len(hull)
    return cx / (3 * area), cy / (3 * area)


class Lift:
    def __init__(self, name, duration, keys, build, view, balance='xy', smooth='minjerk', mirror=False):
        """keys: [(phase, {param: value}, hold)] with phase ascending from 0; loops back to keys[0]."""
        self.name, self.duration, self.keys, self.build = name, duration, keys, build
        self.view, self.balance, self.smooth, self.mirror = view, balance, smooth, mirror

    def state(self, phase):
        phase %= 1.
        keys = self.keys
        if self.smooth == 'hermite':
            params = keys[0][1].keys()
            out = {}
            for p in params:
                if isinstance(keys[0][1][p], (tuple, list)):
                    dims = len(keys[0][1][p])
                    comps = []
                    for d in range(dims):
                        sub = [(t, {p: v[p][d]}, hold) for t, v, hold in keys]
                        comps.append(_hermite_scalar(sub, phase, p))
                    out[p] = tuple(comps)
                else:
                    out[p] = _hermite_scalar(keys, phase, p)
            return out
        i = max(k for k in range(len(keys)) if keys[k][0] <= phase)
        t0, a, _ = keys[i]
        t1, b, _ = keys[(i + 1) % len(keys)]
        if i == len(keys) - 1:
            t1 += 1.
        w = minjerk((phase - t0) / (t1 - t0))
        return {p: _lerp(a[p], b[p], w) for p in a}

    def raw(self, phase, dx=0., dy=0.):
        pose = self.build(self.name, phase, self.state(phase), dx, dy)
        pose.view = dict(self.view)
        return pose

    @cached_property
    def offsets(self):
        n = max(48, round(self.duration * SAMPLES_PER_SECOND))
        n += n % 2
        dt = self.duration / n
        result = [[0., 0.] for _ in range(n)]
        for axis_index, axis in enumerate('xy'):
            if axis not in self.balance:
                continue
            base, zs, gains, targets = [], [], [], []
            for i in range(n):
                phase = i / n
                shift = [0., 0.]
                pose0 = self.raw(phase).result()
                c0 = centre_of_mass(pose0)[0]
                shift[axis_index] = .01
                c1 = centre_of_mass(self.raw(phase, *shift).result())[0]
                base.append(c0[axis_index])
                zs.append(c0[2])
                gains.append((c1[axis_index] - c0[axis_index]) / .01)
                targets.append(_safe_target(pose0, c0)[axis_index])
            zdd = [(zs[(i + 1) % n] - 2 * zs[i] + zs[i - 1]) / dt ** 2 for i in range(n)]
            scale = [zs[i] / max(2., G + zdd[i]) for i in range(n)]
            bdd = [(base[(i + 1) % n] - 2 * base[i] + base[i - 1]) / dt ** 2 for i in range(n)]
            rhs = [targets[i] - base[i] + scale[i] * bdd[i] for i in range(n)]
            off = [-scale[i] * gains[i] / dt ** 2 for i in range(n)]
            diag = [gains[i] - 2 * off[i] for i in range(n)]
            solved = solve_cyclic(off, diag, off, rhs)
            for i in range(n):
                result[i][axis_index] = max(-.2, min(.2, solved[i]))
        if self.mirror:
            # Alternating lifts: the second half is the first half mirrored left-right.
            half = n // 2
            for i in range(half):
                a, b = result[i], result[i + half]
                x, y = (a[0] + b[0]) / 2, (a[1] - b[1]) / 2
                result[i], result[i + half] = [x, y], [x, -y]
        return result

    def pose(self, phase):
        phase %= 1.
        table = self.offsets
        n = len(table)
        x = phase * n
        i = int(x) % n
        u = x - int(x)
        # Periodic Catmull-Rom: smooth second derivative, so the ZMP check sees no kinks.
        p0, p1, p2, p3 = table[i - 1], table[i], table[(i + 1) % n], table[(i + 2) % n]
        dx, dy = (.5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)
                  for a, b, c, d in zip(p0, p1, p2, p3))
        return self.raw(phase, dx, dy)

    def __call__(self, name, phase):
        return self.pose(phase)
