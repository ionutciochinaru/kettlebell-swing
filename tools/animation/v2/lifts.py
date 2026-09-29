"""v2 grinds and holds: deadlift, goblet squat, lunges, rows, side bend, curl.

Every lift carries a 16 kg bell with real proportions; the Lift framework adds
the load-aware hip shift. Fixes follow the baseline reviews (54e441838d09):
arms inside the knees, hanging loads plumb, bells close to the body, elbows at
the flank in curls, deeper side bends and lunges, weight-shift before a foot
leaves the floor.
"""
from math import sin, cos, sqrt, radians

try:
    from ..rig import SIDES, side_sign, add, sub, mul, unit, norm, smooth, ANKLE_HEIGHT, SHOULDER_HALF
    from .common import (BELL, MAX_REACH, trunk, foot, toe_from, stance, leg, reach, handle_grip, one_hand,
                         horns_grip, hang_free)
    from .framework import Lift
except ImportError:
    from rig import SIDES, side_sign, add, sub, mul, unit, norm, smooth, ANKLE_HEIGHT, SHOULDER_HALF
    from v2.common import (BELL, MAX_REACH, trunk, foot, toe_from, stance, leg, reach, handle_grip, one_hand,
                           horns_grip, hang_free)
    from v2.framework import Lift

PACK = radians(7)
LATERAL = SHOULDER_HALF - .045           # shoulder to hand, sideways, for a two-hand handle grip
PLUMB = sqrt(MAX_REACH ** 2 - LATERAL ** 2)


def _elbows_back(p):
    return {s: add(p.j['shoulder_' + s], (-.4, side_sign(s) * .06, -.1)) for s in SIDES}


# ---------------------------------------------------------------- deadlift
DL_STANCE, DL_YAW = .23, radians(16)
# The bell travels straight up and down in front of the hips, between the feet.
DL_FLOOR = (.155, 0., .8 * BELL['radius'] + BELL['handle_to_center'])      # handle when the bell sits on the floor


def _dl_grip(p):
    """Straight arms from the shoulders to the bell's vertical path; the floor stops it."""
    mid = mul(add(p.j['shoulder_l'], p.j['shoulder_r']), .5)
    dx = DL_FLOOR[0] - mid[0]
    drop = sqrt(max(0., (MAX_REACH - .008) ** 2 - LATERAL ** 2 - dx * dx))
    return (DL_FLOOR[0], 0., max(DL_FLOOR[2], mid[2] - drop))


def _dl_build(name, phase, st, dx, dy):
    px, pz = st['pelvis']
    p = trunk(name, phase, (px + dx, dy, pz), st['lean'], pack=(st['pack'], st['pack']))
    stance(p, DL_STANCE, DL_YAW)
    grip = _dl_grip(p)
    handle_grip(p, grip, (0., 0., -1.), poles=_elbows_back(p))
    if grip[2] <= DL_FLOOR[2] + 1e-12:
        p.contacts['kettlebell'] = (DL_FLOOR[0], 0., 0.)
    return p


# Bottom: the bell reached with arms straight; hips back, shoulders over the bell.
_dl_bottom = {'pelvis': (-.22, .60), 'lean': radians(62), 'pack': PACK}
_dl_mid = {'pelvis': (-.15, .74), 'lean': radians(38), 'pack': PACK}
_dl_top = {'pelvis': (0., .915), 'lean': 0., 'pack': PACK}
DEADLIFT = Lift('kb-deadlift', 3.6, [
    (0.00, _dl_bottom, True), (0.10, _dl_bottom, True), (0.30, _dl_mid, False),
    (0.48, _dl_top, True), (0.60, _dl_top, True), (0.82, _dl_mid, False),
], _dl_build, {'azimuth': 30, 'elevation': 10}, balance='x')


# ---------------------------------------------------------------- goblet hold helpers
def _goblet(p):
    up, forward = p.up, p.forward
    center = add(add(p.j['chest'], mul(forward, .205)), mul(up, -.13))
    horns_grip(p, center, up=(0., 0., 1.), across=(0., 1., 0.), height=.55,
               poles={s: add(p.j['shoulder_' + s], (.12, side_sign(s) * .02, -.6)) for s in SIDES})


# ---------------------------------------------------------------- goblet squat
GS_STANCE, GS_YAW = .21, radians(18)


def _gs_build(name, phase, st, dx, dy):
    px, pz = st['pelvis']
    p = trunk(name, phase, (px + dx, dy, pz), st['lean'])
    stance(p, GS_STANCE, GS_YAW)
    _goblet(p)
    return p


_gs_top = {'pelvis': (0., .905), 'lean': radians(4)}
_gs_bottom = {'pelvis': (-.19, .53), 'lean': radians(30)}
GOBLET_SQUAT = Lift('goblet-squat', 3.4, [
    (0.00, _gs_top, True), (0.10, _gs_top, True), (0.46, _gs_bottom, True), (0.54, _gs_bottom, True),
], _gs_build, {'azimuth': 50, 'elevation': 10}, balance='x')


# ---------------------------------------------------------------- reverse lunge (goblet)
RL_WIDTH = .13
RL_TOE_BACK = -.62
RL_PITCH = radians(42)


def _rl_build(name, phase, st, dx, dy):
    rear = 'l' if phase < .5 else 'r'
    front = 'r' if rear == 'l' else 'l'
    sg = side_sign(rear)
    px, pz = st['pelvis']
    p = trunk(name, phase, (px + dx, sg * st['pelvis_y'] + dy, pz), st['lean'])
    front_ankle = (0., side_sign(front) * RL_WIDTH, ANKLE_HEIGHT)
    leg(p, front, foot(p, front, front_ankle))
    step, lift, pitch = st['step'], st['lift'], st['pitch']
    home_toe = add(front_ankle, (0., 0., 0.))
    home_toe = (.16, sg * RL_WIDTH, 0.)
    back_toe = (RL_TOE_BACK, sg * RL_WIDTH, 0.)
    toe = (home_toe[0] + (back_toe[0] - home_toe[0]) * step, sg * RL_WIDTH, lift)
    ankle = toe_from(rear, toe, 0., pitch)
    planted = lift < 1e-9 and (step < 1e-9 or step > 1 - 1e-9)
    direction = foot(p, rear, ankle, 0., pitch, contact=planted)
    # Rear knee turns down toward the floor as the leg steps back; standing, both knees
    # use the same over-the-toes rule (so the side switch at the loop seam is seamless).
    w = smooth(min(1., step * 2.))
    front_pole = add(p.j['hip_' + rear], add(direction, (0., side_sign(rear) * .25, 0.)))
    down_pole = add(p.j['hip_' + rear], (.25, 0., -1.))
    leg(p, rear, direction, pole=tuple(x + (y - x) * w for x, y in zip(front_pole, down_pole)))
    _goblet(p)
    return p


_rl = lambda pelvis, y, lean, step, lift, pitch: {'pelvis': pelvis, 'pelvis_y': y, 'lean': lean, 'step': step,
                                                   'lift': lift, 'pitch': pitch}
# pelvis_y is measured toward the stepping (rear) leg; negative = over the front foot.
_rl_stand = _rl((0., .905), 0., radians(3), 0., 0., 0.)
_rl_shift = _rl((.01, .90), -.12, radians(5), 0., 0., 0.)          # weight over the front foot first
_rl_air = _rl((-.06, .885), -.12, radians(14), .5, .07, radians(22))
_rl_land = _rl((-.14, .83), -.05, radians(18), 1., 0., RL_PITCH)
_rl_bottom = _rl((-.19, .52), -.035, radians(14), 1., 0., RL_PITCH)
_rl_half = [(0.00, _rl_stand, True), (0.03, _rl_stand, True), (0.07, _rl_shift, False), (0.12, _rl_air, False),
            (0.18, _rl_land, False), (0.27, _rl_bottom, True), (0.30, _rl_bottom, True), (0.39, _rl_land, False),
            (0.44, _rl_air, False), (0.47, _rl_shift, False)]
REVERSE_LUNGE = Lift('kb-reverse-lunge', 5.6, _rl_half + [(t + .5, s, h) for t, s, h in _rl_half],
                     _rl_build, {'azimuth': 60, 'elevation': 10}, balance='xy', mirror=True)


# ---------------------------------------------------------------- side lunge (goblet)
SL_WIDTH, SL_YAW = .40, radians(22)


def _sl_build(name, phase, st, dx, dy):
    side = 'l' if phase < .5 else 'r'
    sg = side_sign(side)
    k = st['shift']
    pelvis = (-.15 * k + dx, sg * .25 * k + dy, .86 - .31 * k)
    p = trunk(name, phase, pelvis, radians(24) * k, bend=0., twist=sg * radians(6) * k)
    for s in SIDES:
        ankle = (0., side_sign(s) * SL_WIDTH, ANKLE_HEIGHT)
        direction = foot(p, s, ankle, SL_YAW)
        leg(p, s, direction, out=.2 + (.15 if s == side else -.15) * k)
    _goblet(p)
    return p


_sl_half = [(0.00, {'shift': 0.}, True), (0.05, {'shift': 0.}, True), (0.24, {'shift': 1.}, True),
            (0.29, {'shift': 1.}, True)]
SIDE_LUNGE = Lift('kb-side-lunge', 5.4, _sl_half + [(t + .5, s, h) for t, s, h in _sl_half],
                  _sl_build, {'azimuth': 20, 'elevation': 10}, balance='xy', mirror=True)


# ---------------------------------------------------------------- upright row
UR_STANCE = .14


def _ur_build(name, phase, st, dx, dy):
    k = st['row']
    p = trunk(name, phase, (dx, dy, .905), radians(2), pack=(PACK * (1 - k), PACK * (1 - k)))
    stance(p, UR_STANCE, radians(10))
    chest = p.j['chest']
    bottom = (chest[0] + .205, 0., chest[2] - sqrt(max(.01, MAX_REACH ** 2 - (SHOULDER_HALF - .035) ** 2 - .205 ** 2)) + .01)
    top = (chest[0] + .215, 0., chest[2] - .06)
    grip = tuple(a + (b - a) * k for a, b in zip(bottom, top))
    poles = {s: add(p.j['shoulder_' + s], (-.15 + .05 * k, side_sign(s) * .55, -.3 + .75 * k)) for s in SIDES}
    handle_grip(p, grip, (0., 0., -1.), spacing=.035, poles=poles)
    return p


UPRIGHT_ROW = Lift('kb-upright-row', 3.0, [
    (0.00, {'row': 0.}, True), (0.10, {'row': 0.}, True), (0.45, {'row': 1.}, True), (0.55, {'row': 1.}, True),
], _ur_build, {'azimuth': 35, 'elevation': 10}, balance='x')


# ---------------------------------------------------------------- bent-over row
BR_STANCE = .20


def _br_build(name, phase, st, dx, dy):
    k = st['row']
    p = trunk(name, phase, (-.17 + dx, dy, .80), radians(50), pack=(PACK * (1 - k), PACK * (1 - k)))
    stance(p, BR_STANCE, radians(12))
    chest, up, forward = p.j['chest'], p.up, p.forward
    hang = (chest[0] + .06, 0., chest[2] - PLUMB + .02)
    ribs = add(add(chest, mul(up, -.20)), mul(forward, .07))
    top = (ribs[0] + .04, 0., ribs[2] - .08)
    grip = tuple(a + (b - a) * k for a, b in zip(hang, top))
    poles = {s: add(p.j['shoulder_' + s], (-.2, side_sign(s) * .35, .35 * k - .1)) for s in SIDES}
    handle_grip(p, grip, (0., 0., -1.), poles=poles)
    return p


BENT_ROW = Lift('kb-bent-row', 3.0, [
    (0.00, {'row': 0.}, True), (0.10, {'row': 0.}, True), (0.42, {'row': 1.}, True), (0.52, {'row': 1.}, True),
], _br_build, {'azimuth': 64, 'elevation': 12}, balance='x')


# ---------------------------------------------------------------- side bend (bell in the left hand)
SB_STANCE = .08


def _sb_build(name, phase, st, dx, dy):
    k = st['bend']
    p = trunk(name, phase, (dx, dy, .91), radians(1), bend=radians(24) * k, pack=(radians(10), radians(-2)))
    stance(p, SB_STANCE, radians(8))
    shoulder = p.j['shoulder_l']
    # The loaded arm hangs plumb; the bell rests against the outer thigh and slides down it.
    wrist = add(shoulder, mul(unit((.04, .20, -1.)), MAX_REACH - .004))
    one_hand(p, 'l', wrist, (.05, .22, -1.), pole=add(shoulder, (-.3, .2, 0.)))
    # Free hand on the hip crest, elbow out.
    hip_hand = add(p.j['pelvis'], mul(unit(sub(p.j['hip_r'], p.j['pelvis'])), .19))
    p.arm('r', add(hip_hand, (-.02, -.04, .19)), pole=add(p.j['shoulder_r'], (-.2, -.5, -.2)))
    return p


SIDE_BEND = Lift('kb-side-bend', 3.4, [
    (0.00, {'bend': 0.}, True), (0.10, {'bend': 0.}, True), (0.42, {'bend': 1.}, True), (0.50, {'bend': 1.}, True),
], _sb_build, {'azimuth': 12, 'elevation': 8}, balance='xy')


# ---------------------------------------------------------------- curl (left arm)
CU_STANCE = .14


def _cu_build(name, phase, st, dx, dy):
    k = st['curl']
    p = trunk(name, phase, (dx, dy, .905), radians(0), pack=(radians(6), radians(3)))
    stance(p, CU_STANCE, radians(10))
    # Elbow pinned at the flank; only the forearm moves.
    flex = radians(18) + radians(122) * k
    p.arm_fk('l', shoulder_angle=radians(-2), elbow_flex=flex, outward=.14)
    w = p.j['wrist_l']
    arm = unit(sub(w, p.j['elbow_l']))
    bell_dir = unit((.42 + .48 * k, .30, -1. + .55 * k))
    across = unit((arm[1] * bell_dir[2] - arm[2] * bell_dir[1], arm[2] * bell_dir[0] - arm[0] * bell_dir[2],
                   arm[0] * bell_dir[1] - arm[1] * bell_dir[0]))
    p.j['palm_l'] = w
    handle = [add(w, mul(across, BELL['handle_half'])), add(w, mul(across, -BELL['handle_half']))]
    p.props.append({'type': 'kettlebell', 'center': list(add(w, mul(bell_dir, BELL['handle_to_center']))),
                    'handle': [list(h) for h in handle], 'radius': BELL['radius'], 'mass': BELL['mass'],
                    'grips': {'l': list(w)}})
    hang_free(p, 'r', radians(4), radians(10), .17)
    return p


CURL = Lift('kb-curl', 3.2, [
    (0.00, {'curl': 0.}, True), (0.08, {'curl': 0.}, True), (0.42, {'curl': 1.}, True), (0.52, {'curl': 1.}, True),
], _cu_build, {'azimuth': 70, 'elevation': 10}, balance='x')


LIFTS = {lift.name: lift for lift in (DEADLIFT, GOBLET_SQUAT, REVERSE_LUNGE, SIDE_LUNGE, UPRIGHT_ROW, BENT_ROW,
                                        SIDE_BEND, CURL)}
