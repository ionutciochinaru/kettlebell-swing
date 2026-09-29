"""Shared v2 body, feet, leg and kettlebell-grip builders.

Bells use real 16 kg cast-iron proportions and carry their mass, so balance and
the drawn model agree. Grips are exact: wrists sit on the handle (or horns) and
the validator checks it.
"""
from math import sin, cos, sqrt, radians

try:
    from ..rig import (Pose, SIDES, ANKLE_HEIGHT, SHOULDER_HALF, UPPER_ARM, FOREARM, HIP_HALF, THIGH, SHIN,
                       side_sign, add, sub, mul, unit, cross, dot, norm, rotate_y)
except ImportError:
    from rig import (Pose, SIDES, ANKLE_HEIGHT, SHOULDER_HALF, UPPER_ARM, FOREARM, HIP_HALF, THIGH, SHIN,
                     side_sign, add, sub, mul, unit, cross, dot, norm, rotate_y)

BELL = {'mass': 16., 'radius': .105, 'handle_to_center': .165, 'handle_half': .095}
MAX_REACH = UPPER_ARM + FOREARM - .006
HORN_ROOT = (.62, .74)        # horn root on the body, in bell radii (across, up)


def trunk(name, phase, pelvis, lean=0., bend=0., twist=0., pack=(0., 0.)):
    """Torso: sagittal lean (forward +), lateral bend (toward +y = left), twist about the trunk.

    pack[side] rotates that clavicle down (radians); lengths stay exact.
    """
    up = unit((sin(lean) * cos(bend), sin(bend), cos(lean) * cos(bend)))
    p = Pose(name, phase).torso(pelvis, up=up)
    up = p.up
    base = sub((0., 1., 0.), mul(up, dot((0., 1., 0.), up)))
    lateral = unit(base)
    if twist:
        c, s = cos(twist), sin(twist)
        lateral = add(add(mul(lateral, c), mul(cross(up, lateral), s)), mul(up, dot(up, lateral) * (1 - c)))
    for i, s in enumerate(SIDES):
        a = pack[i]
        direction = add(mul(lateral, side_sign(s) * cos(a)), mul(up, -sin(a)))
        p.j['shoulder_' + s] = add(p.j['chest'], mul(direction, SHOULDER_HALF))
    p.forward = unit(cross(lateral, up))
    p.j['face'] = add(p.j['head'], mul(p.forward, .075))
    return p


def foot(p, s, ankle, yaw=0., pitch=0., contact=True):
    """Foot with toe-out yaw (outward +) and pitch about the forefoot (heel up +)."""
    sg = side_sign(s)
    yaw = sg * yaw

    def place(v):
        v = rotate_y(v, pitch)
        return (v[0] * cos(yaw) - v[1] * sin(yaw), v[0] * sin(yaw) + v[1] * cos(yaw), v[2])
    toe = add(ankle, place((.16, 0., -ANKLE_HEIGHT)))
    heel = add(ankle, place((-.075, 0., -ANKLE_HEIGHT)))
    p.j['ankle_' + s], p.j['toe_' + s], p.j['heel_' + s] = tuple(ankle), toe, heel
    if contact:
        p.contacts['toe_' + s] = toe
        if abs(pitch) < 1e-7:
            p.contacts['heel_' + s] = heel
    return (cos(yaw), sin(yaw), 0.)


def toe_from(s, toe, yaw=0., pitch=0.):
    """Ankle position that puts the toe exactly at `toe` (for a planted forefoot)."""
    sg = side_sign(s)
    y = sg * yaw
    v = rotate_y((.16, 0., -ANKLE_HEIGHT), pitch)
    v = (v[0] * cos(y) - v[1] * sin(y), v[0] * sin(y) + v[1] * cos(y), v[2])
    return sub(toe, v)


def stance(p, width, yaw=radians(14), x=0.):
    """Both feet planted, ankles `width` from the midline; knees track over the toes."""
    for s in SIDES:
        ankle = (x, side_sign(s) * width, ANKLE_HEIGHT)
        direction = foot(p, s, ankle, yaw)
        leg(p, s, direction)


def leg(p, s, toe_direction, out=.25, pole=None):
    hip = p.j['hip_' + s]
    pole = pole or add(hip, add(toe_direction, (0., side_sign(s) * out, 0.)))
    p.leg(s, p.j['ankle_' + s], pole=pole)


def reach(shoulder, target, limit=MAX_REACH):
    offset = sub(target, shoulder)
    d = norm(offset)
    return target if d <= limit else add(shoulder, mul(offset, limit / d))


def _bell(center, handle, grips, horns=None, grip_joint='wrist'):
    prop = {'type': 'kettlebell', 'center': list(center), 'handle': [list(h) for h in handle],
            'radius': BELL['radius'], 'mass': BELL['mass'], 'grips': {s: list(g) for s, g in grips.items()}}
    if horns:
        prop['horns'] = [[list(a), list(b)] for a, b in horns]
        prop['grip_joint'] = grip_joint
    return prop


def handle_grip(p, grip, bell_dir, across=(0., 1., 0.), spacing=.045, poles=None):
    """Both hands side by side on the handle; the bell hangs from it along bell_dir."""
    across = unit(across)
    bell_dir = unit(bell_dir)
    grips = {s: add(grip, mul(across, side_sign(s) * spacing)) for s in SIDES}
    for s in SIDES:
        pole = (poles or {}).get(s) or add(p.j['shoulder_' + s], (-.3, side_sign(s) * .25, -.25))
        p.arm(s, grips[s], pole=pole, palm=grips[s])
    handle = [add(grip, mul(across, BELL['handle_half'])), add(grip, mul(across, -BELL['handle_half']))]
    p.props.append(_bell(add(grip, mul(bell_dir, BELL['handle_to_center'])), handle, grips))


def one_hand(p, s, wrist, bell_dir, pole):
    """Single-hand grip at the handle centre; the bell hangs along bell_dir."""
    wrist = reach(p.j['shoulder_' + s], wrist)
    p.arm(s, wrist, pole=pole, palm=wrist)
    w = p.j['wrist_' + s]
    arm = unit(sub(w, p.j['elbow_' + s]))
    bell_dir = unit(bell_dir)
    # The bell body can rotate around the handle but never folds back onto the forearm.
    back = dot(bell_dir, mul(arm, -1.))
    if back > .15:
        bell_dir = unit(add(bell_dir, mul(arm, back - .15)))
    across = cross(bell_dir, arm)
    if norm(across) < 1e-6:
        across = cross(bell_dir, (0., 1., 0.))
    across = unit(across)
    handle = [add(w, mul(across, BELL['handle_half'])), add(w, mul(across, -BELL['handle_half']))]
    p.props.append(_bell(add(w, mul(bell_dir, BELL['handle_to_center'])), handle, {s: w}))


def horns_grip(p, center, up=(0., 0., 1.), across=(0., 1., 0.), height=.62, poles=None):
    """Bell held by the horns (goblet): upright, base down, hands around the horns.

    `height` places each hand along its horn from root (0) to handle corner (1).
    """
    r = BELL['radius']
    up, across = unit(up), unit(across)
    handle = [add(add(center, mul(up, BELL['handle_to_center'])), mul(across, sg * BELL['handle_half'])) for sg in (1, -1)]
    roots = [add(add(center, mul(up, HORN_ROOT[1] * r)), mul(across, sg * HORN_ROOT[0] * r)) for sg in (1, -1)]
    grips = {}
    for i, s in enumerate(SIDES):
        grips[s] = add(roots[i], mul(sub(handle[i], roots[i]), height))
        pole = (poles or {}).get(s) or add(p.j['shoulder_' + s], (.05, side_sign(s) * .12, -.6))
        p.arm(s, grips[s], pole=pole, palm=grips[s])
    p.props.append(_bell(center, handle, grips, horns=list(zip(roots, handle))))


def hang_free(p, s, angle=radians(6), elbow=radians(10), outward=.12):
    p.arm_fk(s, shoulder_angle=angle, elbow_flex=elbow, outward=outward)
