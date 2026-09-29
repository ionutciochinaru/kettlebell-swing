"""v2 single-arm lifts (left arm): clean, press, snatch.

Hand targets are authored relative to the chest, so the load-aware hip shift
and the hinge carry the arm with the trunk. Flowing lifts use a periodic
Hermite spline (continuous velocity; 'hold' keys stop exactly).
Baseline fixes: the backswing runs through the midline between the knees with
the hand at the groin; the clean pulls the elbow back and in; the rack forearm
is vertical with the elbow under the wrist; the press keeps the wrist stacked
over the elbow; the snatch punch-through passes wide of the head.
"""
from math import sin, cos, radians

try:
    from ..rig import SIDES, side_sign, add, sub, mul, unit
    from .common import MAX_REACH, trunk, stance, one_hand
    from .framework import Lift
except ImportError:
    from rig import SIDES, side_sign, add, sub, mul, unit
    from v2.common import MAX_REACH, trunk, stance, one_hand
    from v2.framework import Lift

ARM, FREE = 'l', 'r'
STANCE, YAW = .30, radians(18)
PACK = radians(6)


def _pelvis(h):
    return (-.25 * h, 0., .905 - .075 * h), radians(64) * h


def _build(name, phase, st, dx, dy):
    (px, py, pz), lean = _pelvis(st['hinge'])
    p = trunk(name, phase, (px + dx, py + dy, pz), lean, pack=(PACK * st['pack'], radians(2)))
    stance(p, STANCE, YAW)
    chest = p.j['chest']
    shoulder = p.j['shoulder_' + ARM]
    wrist = add(chest, st['wrist'])
    pole = add(shoulder, st['pole'])
    arm = unit(sub(wrist, shoulder))
    if len(st['bell']) == 2:
        # Relative to the arm: angle from the arm line toward the back of the hand, plus a sideways lean.
        angle, lateral = radians(st['bell'][0]), st['bell'][1]
        back = unit((-arm[2], 0., arm[0]))
        bell = add(add(mul(arm, cos(angle)), mul(back, sin(angle))), (0., lateral, 0.))
    else:
        # When the arm points down the bell trails along it (it hangs from the handle).
        down = max(0., -arm[2])
        bell = add(unit(st['bell']), mul(arm, 1.4 * down))
    one_hand(p, ARM, wrist, bell, pole)
    # Free arm hangs plumb and slightly out, following the hinge.
    p.arm_fk(FREE, shoulder_angle=radians(6), elbow_flex=radians(14), outward=.20)
    return p


def key(t, hinge, wrist, pole, bell, pack=1., hold=False):
    return (t, {'hinge': hinge, 'wrist': wrist, 'pole': pole, 'bell': bell, 'pack': pack}, hold)


# Chest-relative targets (m). Standing chest is ~1.33 m high; shoulder at +0.19 y.
RACK = dict(wrist=(.20, .08, 0.), pole=(.20, -.05, -.75), bell=(.30, 1., -.30))
LOCK_DIR = unit((.03, .05, 1.))
LOCKOUT = dict(wrist=add((0., .19, 0.), mul(LOCK_DIR, MAX_REACH - .004)), pole=(-.35, .30, .10),
               bell=(-.75, .45, -.25))
BACK = dict(wrist=(-.22, .02, -.30), pole=(-.35, .10, .10), bell=(-.55, .12, -.85))
DRIVE = dict(wrist=(.30, .03, -.47), pole=(-.35, .10, .10), bell=(.35, 0., -1.))


def _k(t, hinge, spec, pack=1., hold=False, **override):
    s = dict(spec, **override)
    return key(t, hinge, s['wrist'], s['pole'], s['bell'], pack, hold)


CLEAN = Lift('kb-clean', 2.6, [
    _k(0.00, 0., RACK, 0., True), _k(0.14, 0., RACK, 0., True),
    # Uncurl close to the body into the hinge.
    _k(0.30, .45, dict(wrist=(.18, .04, -.42), pole=(-.3, .08, .05), bell=(.05, 0., -1.))),
    _k(0.45, 1., BACK, 1., True),
    _k(0.60, .06, DRIVE),
    # Elbow back and in, hand up the body; the bell stays close.
    _k(0.73, 0., dict(wrist=(.17, .10, -.20), pole=(-.35, .02, -.35), bell=(.08, .15, -1.))),
    # Hand comes around the bell into the rack.
    _k(0.86, 0., dict(wrist=(.20, .10, -.08), pole=(.15, -.05, -.7), bell=(.25, .9, -.5)), .5),
], _build, {'azimuth': 40, 'elevation': 10}, smooth='hermite')


PRESS = Lift('kb-press', 3.2, [
    _k(0.00, 0., RACK, 0., True), _k(0.12, 0., RACK, 0., True),
    # Wrist stacked over the elbow; elbow ~35 degrees in front of the frontal plane.
    _k(0.30, 0., dict(wrist=(.10, .19, .20), pole=(.22, .10, -.75), bell=(-.45, .85, -.3)), 0.),
    _k(0.44, 0., LOCKOUT, 0., True), _k(0.58, 0., LOCKOUT, 0., True),
    _k(0.80, 0., dict(wrist=(.10, .19, .20), pole=(.22, .10, -.75), bell=(-.45, .85, -.3)), 0.),
], _build, {'azimuth': 36, 'elevation': 8}, smooth='hermite')


SNATCH_LOCK = dict(LOCKOUT, bell=(110., .45))
SNATCH = Lift('kb-snatch', 2.6, [
    _k(0.00, 0., SNATCH_LOCK, 0., True), _k(0.10, 0., SNATCH_LOCK, 0., True),
    # Turn the bell over beside the head and let it drop close to the body.
    _k(0.27, .2, dict(wrist=(.30, .26, -.12), pole=(-.25, .45, .0), bell=(40., .45))),
    _k(0.44, 1., dict(BACK, wrist=(-.22, .026, -.30), bell=(0., .07)), 1., True),
    _k(0.58, .06, dict(DRIVE, bell=(0., .05))),
    # High pull: elbow up and back, bell hanging close below the hand.
    _k(0.70, 0., dict(wrist=(.24, .20, .02), pole=(-.2, .45, .25), bell=(-70., .25))),
    # Punch through wide of the head as the bell floats over onto the forearm.
    _k(0.82, 0., dict(wrist=(.14, .30, .36), pole=(-.3, .45, .1), bell=(60., .40))),
], _build, {'azimuth': 40, 'elevation': 10}, smooth='hermite')


SINGLE_ARM = {lift.name: lift for lift in (CLEAN, PRESS, SNATCH)}
