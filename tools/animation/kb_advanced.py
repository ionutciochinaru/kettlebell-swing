"""Single-arm kettlebell lifts and the Turkish get-up on the fixed-length rig.

Clean, press and snatch are shown on the left arm, which is the camera-near side
in both the watch renderer and the app's default view. Each loop is one rep of
one side; the app counts these per side.

Ballistic lifts use a periodic non-uniform Hermite spline through authored key
poses, so velocity is continuous (including across the loop seam) and 'hold'
keys stop exactly. The get-up uses eased piecewise keys: it is performed as
distinct, deliberate steps, and pinned floor contacts stay exactly fixed.
Exact paths and timings are production choices, not prescribed ranges of motion.
"""
from math import sin, cos, pi, sqrt

try:
    from .rig import *
except ImportError:
    from rig import *

BELL_RADIUS = .095
HANDLE_HALF = .075
HANDLE_TO_BELL = .13
MAX_REACH = UPPER_ARM + FOREARM - .007


# ----------------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------------

def vlerp(a, b, t):
    return tuple(x+(y-x)*t for x, y in zip(a, b))


def clamp_reach(shoulder, target, reach=MAX_REACH):
    offset = sub(target, shoulder)
    distance = norm(offset)
    return target if distance <= reach else add(shoulder, mul(offset, reach/distance))


def single_bell(p, s, v):
    """Attach a bell to one hand. `v` points from the handle to the bell body."""
    wrist = p.j['wrist_'+s]
    arm = unit(sub(wrist, p.j['elbow_'+s]))
    v = unit(v)
    across = cross(v, arm)
    if norm(across) < 1e-6:
        across = cross(v, (0, 1, 0))
    across = unit(across)
    handle = [add(wrist, mul(across, HANDLE_HALF)), add(wrist, mul(across, -HANDLE_HALF))]
    p.props.append({'type': 'kettlebell', 'center': list(add(wrist, mul(v, HANDLE_TO_BELL))),
                    'handle': [list(h) for h in handle], 'radius': BELL_RADIUS,
                    'grips': {s: list(wrist)}})


def lockout_bell(arm_dir, facing, lateral_out):
    """Overhead or pressed: the bell rests on the back of the forearm."""
    return unit(add(add(mul(arm_dir, -.6), mul(facing, -.6)), mul(lateral_out, .25)))


def periodic_hermite(keys, phase):
    """keys: [(time, vector, hold)], times ascending in [0,1). C1 periodic.

    Tangents follow non-uniform Catmull-Rom; hold keys have zero tangent, so two
    equal adjacent hold keys give an exactly still segment.
    """
    n = len(keys)
    times = [k[0] for k in keys]
    values = [k[1] for k in keys]

    def time(i):
        return times[i % n] + (i // n)

    def tangent(i):
        if keys[i % n][2]:
            return tuple(0. for _ in values[0])
        prev_v, next_v = values[(i-1) % n], values[(i+1) % n]
        dt = time(i+1) - time(i-1)
        return tuple((b-a)/dt for a, b in zip(prev_v, next_v))

    phase %= 1.
    i = max(k for k in range(n) if times[k] <= phase) if phase >= times[0] else -1
    t0, t1 = time(i), time(i+1)
    if i < 0:
        t0, t1 = times[-1]-1, times[0]
    h = t1 - t0
    u = (phase - t0)/h
    p0, p1 = values[i % n], values[(i+1) % n]
    m0, m1 = tangent(i), tangent(i+1)
    h00, h10 = 2*u**3-3*u**2+1, u**3-2*u**2+u
    h01, h11 = -2*u**3+3*u**2, u**3-u**2
    return tuple(h00*a + h10*h*ma + h01*b + h11*h*mb for a, b, ma, mb in zip(p0, p1, m0, m1))


# ----------------------------------------------------------------------------
# Standing single-arm lifts (left hand)
# ----------------------------------------------------------------------------

ARM = 'l'
FREE = 'r'
FACING = (1, 0, 0)
OUT = (0, 1, 0)       # lateral, away from the midline, for the left arm


def hinge_pelvis(hinge):
    """Same hinge family as the two-hand swing: hips back and down, trunk forward."""
    return (-.20*hinge, 0, .945-.17*hinge), radians(65)*hinge


def standing_single(name, phase, keys, view):
    """keys vector: hinge, wrist(x,y,z), pole offset from shoulder(x,y,z), bell dir v(x,y,z)."""
    hinge, wx, wy, wz, px, py, pz, vx, vy, vz = periodic_hermite(keys, phase)
    hinge = clamp(hinge, 0., 1.)
    pelvis, lean = hinge_pelvis(hinge)
    p = standing(name, phase, pelvis=pelvis, lean=lean, foot_y=.20)
    shoulder = p.j['shoulder_'+ARM]
    wrist = clamp_reach(shoulder, (wx, wy, wz))
    p.arm(ARM, wrist, pole=add(shoulder, (px, py, pz)), palm=wrist)
    # The free arm hangs in world vertical, slightly out, and follows the hinge.
    p.arm_fk(FREE, shoulder_angle=radians(8)+radians(25)*hinge, elbow_flex=radians(12), outward=.22)
    single_bell(p, ARM, (vx, vy, vz))
    p.view = view
    return p


def _chest(hinge):
    pelvis, lean = hinge_pelvis(hinge)
    return add(pelvis, mul((sin(lean), 0, cos(lean)), TORSO))


def _shoulder(hinge):
    return add(_chest(hinge), (0, SHOULDER_HALF, 0))


def _hang(hinge, angle_deg, toward_mid=.13, reach=MAX_REACH):
    """Long arm from the shoulder at `angle_deg` from world-down (positive = forward)."""
    a = radians(angle_deg)
    direction = unit((sin(a), -toward_mid, -cos(a)))
    return add(_shoulder(hinge), mul(direction, reach)), direction


RACK_WRIST = (.14, .075, 1.30)
RACK_POLE = (.22, -.03, -.55)
RACK_BELL = (-.45, 1., -.55)
LOCKOUT_DIR = unit((.03, .03, 1))
LOCKOUT_WRIST = add(_shoulder(0), mul(LOCKOUT_DIR, MAX_REACH))
LOCKOUT_POLE = (-.35, .30, .10)
LOCKOUT_BELL = lockout_bell(LOCKOUT_DIR, FACING, OUT)


def _key(time, hinge, wrist, pole, bell, hold=False):
    return (time, (hinge, *wrist, *pole, *bell), hold)


def _swing_keys():
    """Backswing and hip drive shared by clean and snatch: bell trails the long arm."""
    back, back_dir = _hang(1., -28)
    drive, drive_dir = _hang(.05, 18)
    return back, back_dir, drive, drive_dir


def kb_clean(name, phase):
    back, back_dir, drive, drive_dir = _swing_keys()
    drop, drop_dir = _hang(.45, 5)
    keys = [
        _key(.00, 0., RACK_WRIST, RACK_POLE, RACK_BELL, hold=True),
        _key(.14, 0., RACK_WRIST, RACK_POLE, RACK_BELL, hold=True),
        # Uncurl and let the bell drop close to the body into the hinge.
        _key(.30, .45, drop, (-.30, .10, .10), drop_dir),
        _key(.45, 1., back, (-.30, .10, .10), back_dir, hold=True),
        # Hips snap; the arm stays long, then the elbow pulls back and in.
        _key(.60, .05, drive, (-.30, .10, .10), drive_dir),
        _key(.74, 0., (.17, .15, 1.13), (-.20, .45, .05), (.05, .25, -1.)),
        # The hand comes around the bell; it lands softly on the forearm.
        _key(.87, 0., (.16, .10, 1.26), RACK_POLE, (-.20, .80, -.80)),
    ]
    return standing_single(name, phase, keys, {'azimuth': 40, 'elevation': 10})


def kb_press(name, phase):
    keys = [
        _key(.00, 0., RACK_WRIST, RACK_POLE, RACK_BELL, hold=True),
        _key(.12, 0., RACK_WRIST, RACK_POLE, RACK_BELL, hold=True),
        # Forearm stays vertical under the bell as it passes the face.
        _key(.30, 0., (.10, .20, 1.56), (.10, .55, -.25), lockout_bell((0, 0, 1), FACING, OUT)),
        _key(.44, 0., LOCKOUT_WRIST, LOCKOUT_POLE, LOCKOUT_BELL, hold=True),
        _key(.60, 0., LOCKOUT_WRIST, LOCKOUT_POLE, LOCKOUT_BELL, hold=True),
        _key(.80, 0., (.10, .20, 1.56), (.10, .55, -.25), lockout_bell((0, 0, 1), FACING, OUT)),
    ]
    return standing_single(name, phase, keys, {'azimuth': 36, 'elevation': 8})


def kb_snatch(name, phase):
    back, back_dir, drive, drive_dir = _swing_keys()
    keys = [
        _key(.00, 0., LOCKOUT_WRIST, LOCKOUT_POLE, LOCKOUT_BELL, hold=True),
        _key(.12, 0., LOCKOUT_WRIST, LOCKOUT_POLE, LOCKOUT_BELL, hold=True),
        # Turn the bell over and let it fall into the backswing.
        _key(.28, .20, (.36, .12, 1.22), (-.25, .35, -.05), (.25, .15, -1.)),
        _key(.44, 1., back, (-.30, .10, .10), back_dir, hold=True),
        _key(.58, .05, drive, (-.30, .10, .10), drive_dir),
        # High pull: elbow up and back, bell close to the body.
        _key(.70, 0., (.24, .16, 1.32), (-.15, .45, .20), (.10, .20, -1.)),
        # Punch through as the bell floats, then lock out.
        _key(.82, 0., (.12, .12, 1.70), (-.30, .35, .05), (-.40, .20, -.80)),
    ]
    return standing_single(name, phase, keys, {'azimuth': 40, 'elevation': 10})


# ----------------------------------------------------------------------------
# Turkish get-up (bell in the left hand, right hand and left foot support)
# ----------------------------------------------------------------------------

BELL = 'l'
SUPPORT = 'r'
FLOOR_PELVIS = .10         # joint centre height when lying on the back
FOOT_L = (.40, .17, ANKLE_HEIGHT)      # bell-side foot, planted from start to stand
HEEL_LEG_ANKLE = (.58, -.62, .075)     # straight support leg, heel on the floor
HAND = (-.06, -.56, .032)              # support hand wrist, posted on the floor
HAND_PALM = (-.005, -.575, .02)
KNEE = (-.02, -.30, .048)              # support knee on the floor after the sweep
KNEEL_PITCH = radians(26)


def rotate_about(v, axis, angle):
    c, s = cos(angle), sin(angle)
    return add(add(mul(v, c), mul(cross(axis, v), s)), mul(axis, dot(axis, v)*(1-c)))


def trunk(p, pelvis, up, twist):
    """Torso with shoulders rotated `twist` radians about the trunk axis."""
    p.torso(pelvis, up=up)
    up = p.up
    base = sub((0, 1, 0), mul(up, dot((0, 1, 0), up)))
    lateral = rotate_about(unit(base), up, twist)
    for s in SIDES:
        p.j['shoulder_'+s] = add(p.j['chest'], mul(lateral, side_sign(s)*SHOULDER_HALF))
    p.forward = unit(cross(lateral, up))
    p.j['face'] = add(p.j['head'], mul(p.forward, .075))


# Key poses. Each: pelvis, trunk up, twist, support leg mode, support arm mode.
# 'kneel' keys derive the pelvis from the pinned knee so the knee never slides.
def kneel_pelvis(thigh_dir):
    hip = add(KNEE, mul(unit(thigh_dir), THIGH))
    return sub(hip, (0, side_sign(SUPPORT)*HIP_HALF, 0))


GETUP = [
    # time, name, params
    (0.00, 'lying', dict(pelvis=(0, 0, FLOOR_PELVIS), up=(-1, 0, 0), twist=0., leg='straight', hand='floor')),
    (0.07, 'lying', dict(pelvis=(0, 0, FLOOR_PELVIS), up=(-1, 0, 0), twist=0., leg='straight', hand='floor')),
    (0.15, 'elbow', dict(pelvis=(0, 0, FLOOR_PELVIS), up=unit((-.86, -.28, .43)), twist=radians(-22), leg='straight', hand='floor')),
    (0.23, 'hand', dict(pelvis=(0, 0, FLOOR_PELVIS), up=unit((-.50, -.20, .84)), twist=radians(-14), leg='straight', hand='floor')),
    (0.31, 'bridge', dict(pelvis=(.08, -.02, .40), up=unit((-.72, -.52, .46)), twist=radians(-10), leg='straight', hand='floor')),
    (0.40, 'sweep', dict(thigh=(.10, .14, .98), up=unit((-.35, -.80, .50)), twist=radians(-8), leg='kneel', shin=(-.35, -.90, .25), hand='floor')),
    (0.48, 'kneel', dict(thigh=(.02, .02, 1.), up=(0, 0, 1), twist=0., leg='kneel', shin=(-1, -.02, .25), hand='free')),
    (0.50, 'kneel', dict(thigh=(.02, .02, 1.), up=(0, 0, 1), twist=0., leg='kneel', shin=(-1, -.02, .25), hand='free')),
    (0.60, 'stand', dict(pelvis=(.40, 0, .945), up=(0, 0, 1), twist=0., leg='stand', hand='free')),
    (0.66, 'stand', dict(pelvis=(.40, 0, .945), up=(0, 0, 1), twist=0., leg='stand', hand='free')),
]
def getup_keys():
    """Ascent as authored, then the same poses in reverse to lie back down."""
    ascent = GETUP
    top = ascent[-1][0]
    span = 1. - top
    # Map the descent onto [top, 1): reverse order, same relative spacing.
    rise = ascent[-2][0]
    descent = []
    rungs = [k for k in ascent[:-1]][::-1]
    total = rise - ascent[0][0]
    for t, name, params in rungs:
        descent.append((top + span*(rise - t)/total, name, params))
    return ascent + descent[1:]


KEYS = getup_keys()


def _pelvis(params):
    return kneel_pelvis(params['thigh']) if 'thigh' in params else params['pelvis']


def _interp_params(a, b, u):
    out = {'twist': a['twist'] + (b['twist']-a['twist'])*u,
           'up': unit(vlerp(a['up'], b['up'], u))}
    if 'thigh' in a and 'thigh' in b:
        out['thigh'] = unit(vlerp(a['thigh'], b['thigh'], u))
        out['pelvis'] = kneel_pelvis(out['thigh'])
    else:
        out['pelvis'] = vlerp(_pelvis(a), _pelvis(b), u)
    if 'shin' in a and 'shin' in b:
        out['shin'] = unit(vlerp(a['shin'], b['shin'], u))
    return out


def support_leg(p, mode_a, mode_b, u, params_a, params_b, out):
    """Straight leg with heel down, kneeling shin, or standing foot."""
    s = SUPPORT
    hip = p.j['hip_'+s]
    if mode_a == mode_b == 'straight':
        ankle = p.foot(s, ankle=HEEL_LEG_ANKLE, pitch=-pi/2, contact=False)
        p.contacts['heel_'+s] = p.j['heel_'+s]
        p.leg(s, ankle, pole=add(hip, (0, 0, 1)))
        return
    if mode_a == mode_b == 'kneel':
        ankle = add(KNEE, mul(out['shin'], SHIN))
        # Toes tucked under, heel raised.
        p.foot(s, ankle=ankle, pitch=KNEEL_PITCH, contact=False)
        p.leg(s, ankle, pole=KNEE)
        p.contacts['knee_'+s] = p.j['knee_'+s]
        return
    if mode_a == mode_b == 'stand':
        ankle = p.foot(s, ankle=(.40, -.17, ANKLE_HEIGHT))
        p.leg(s, ankle)
        return
    # Transition between modes: move the ankle along an arc, pole blends toward the target knee.
    def ankle_for(mode, params):
        if mode == 'straight':
            return HEEL_LEG_ANKLE, radians(-90)
        if mode == 'kneel':
            return add(KNEE, mul(unit(params['shin']), SHIN)), KNEEL_PITCH
        return (.40, -.17, ANKLE_HEIGHT), 0.
    (a0, pitch0), (a1, pitch1) = ankle_for(mode_a, params_a), ankle_for(mode_b, params_b)
    lift = .12*sin(pi*u)
    ankle = add(vlerp(a0, a1, u), (0, 0, lift))
    p.foot(s, ankle=ankle, pitch=pitch0+(pitch1-pitch0)*u, contact=False)
    pole_up = add(hip, (0, 0, 1))
    pole = vlerp(pole_up, KNEE, u) if mode_b == 'kneel' else vlerp(KNEE if mode_a == 'kneel' else pole_up, add(hip, (1, 0, 0)), u)
    p.leg(s, ankle, pole=pole)


def support_arm(p, mode_a, mode_b, u):
    s = SUPPORT
    shoulder = p.j['shoulder_'+s]
    # Elbow bends out to the side and back, so the forearm lowers toward the
    # floor during the roll without passing through it.
    below = add(shoulder, (-.25, -.6, -.05))
    if mode_a == mode_b == 'floor':
        p.arm(s, HAND, pole=below, palm=HAND_PALM, contact=True)
        return
    free_fk = Pose('tmp', 0).torso(p.j['pelvis'])
    free_fk.j['shoulder_'+s] = shoulder
    free_fk.arm_fk(s, shoulder_angle=radians(18), elbow_flex=radians(14), outward=.35)
    free = free_fk.j['wrist_'+s]
    if mode_a == mode_b == 'free':
        p.arm(s, free, pole=add(shoulder, (-.3, -.3, -.3)))
        return
    t = u if mode_a == 'floor' else 1-u
    wrist = clamp_reach(shoulder, add(vlerp(HAND, free, smooth(t)), (0, 0, .10*sin(pi*t))))
    p.arm(s, wrist, pole=vlerp(below, add(shoulder, (-.3, -.3, -.3)), t))
    # Peel the flat palm off the floor into the hand's rest direction.
    wrist = p.j['wrist_'+s]
    rest = mul(unit(sub(wrist, p.j['elbow_'+s])), .065)
    p.j['palm_'+s] = add(wrist, vlerp(sub(HAND_PALM, HAND), rest, smooth(t)))


def kb_getup(name, phase):
    phase %= 1.
    index = max(i for i, k in enumerate(KEYS) if k[0] <= phase)
    ta, _, a = KEYS[index]
    tb, _, b = KEYS[(index+1) % len(KEYS)]
    if index == len(KEYS)-1:
        tb += 1.
    u = smooth((phase-ta)/(tb-ta))
    out = _interp_params(a, b, u)

    p = Pose(name, phase)
    trunk(p, out['pelvis'], out['up'], out['twist'])

    # Bell-side leg: foot planted throughout; knee points up while lying.
    ankle = p.foot(BELL, ankle=FOOT_L)
    p.leg(BELL, ankle, pole=add(p.j['hip_'+BELL], (.3, .15, 1)))

    support_leg(p, a['leg'], b['leg'], u, a, b, out)
    support_arm(p, a['hand'], b['hand'], u)

    # Bell arm stays vertical over the shoulder the whole way.
    shoulder = p.j['shoulder_'+BELL]
    wrist = add(shoulder, (0, 0, MAX_REACH))
    p.arm(BELL, wrist, pole=add(shoulder, (-.3, .3, .1)), palm=wrist)
    single_bell(p, BELL, lockout_bell((0, 0, 1), FACING, (0, 1, 0)))
    p.view = {'azimuth': 48, 'elevation': 26}
    return p


ADVANCED_MOTIONS = {'kb-clean': kb_clean, 'kb-press': kb_press,
                    'kb-snatch': kb_snatch, 'kb-getup': kb_getup}
