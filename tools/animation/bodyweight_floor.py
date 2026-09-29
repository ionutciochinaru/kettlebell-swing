"""Offline floor and plank moves from the bodyweight chart (P18 batch 3).

Sources S37-S60 in docs/animation-review/form-research.md; chart-defined moves
are marked in their docstrings. Built on the fixed-length rig and the stretch /
push-up helpers. No watch-side code.
"""
from math import sin, cos, pi, sqrt, asin
try:
    from .rig import *
    from .stretches import (rotate, mix_point, stage, set_head, hold_cycle, ease_hold,
                            alternating, articulate, supine, kneel_on_all_fours, hands_under_shoulders)
    from .pushups import plank_body, plant_hands, press_angle, knee_drive, two_reps, TOP
except ImportError:
    from rig import *
    from stretches import (rotate, mix_point, stage, set_head, hold_cycle, ease_hold,
                           alternating, articulate, supine, kneel_on_all_fours, hands_under_shoulders)
    from pushups import plank_body, plant_hands, press_angle, knee_drive, two_reps, TOP

def asin_clamped(x):
    return asin(max(-1., min(1., x)))


SUPINE_VIEW = {'azimuth': 78, 'elevation': 12}
PLANK_VIEW = {'azimuth': 66, 'elevation': 16}


def toward_head(angle):
    """Direction from the pelvis toward the head for a supine trunk lifted `angle` off the floor."""
    return (-cos(angle), 0, sin(angle))


def curl(p, lower, upper):
    """Supine trunk curl: lower/upper spine lift angles (radians) from the floor."""
    articulate(p, toward_head(lower), toward_head(upper))
    return p


def hands_behind_head(p):
    up, forward = p.up, p.forward
    side = unit(cross(up, forward))
    for s in SIDES:
        sg = side_sign(s)
        wrist = add(add(p.j['head'], mul(forward, -.07)), mul(side, sg*.07))
        p.arm(s, wrist, pole=add(p.j['shoulder_'+s], add(mul(side, sg*.6), mul(forward, .1))))
    return p


def arms_along_floor(p):
    """Straight arms resting on the floor beside the body, palms down."""
    for s in SIDES:
        shoulder = p.j['shoulder_'+s]
        # Out beside the hips, clear of the legs.
        d = unit((1, side_sign(s)*.42, min(0., .035-shoulder[2])))
        p.j['elbow_'+s] = add(shoulder, mul(d, UPPER_ARM))
        wrist = add(shoulder, mul(d, UPPER_ARM+FOREARM))
        p.j['wrist_'+s] = (wrist[0], wrist[1], max(wrist[2], .03))
        p.j['palm_'+s] = add(p.j['wrist_'+s], mul(d, .065))
        p.contacts['palm_'+s] = p.j['palm_'+s]
    return p


def feet_planted(p, x=.36):
    for s in SIDES:
        ankle = p.foot(s, ankle=(x, side_sign(s)*HIP_HALF, ANKLE_HEIGHT))
        p.leg(s, ankle, pole=add(p.j['hip_'+s], (0, 0, 1)))
    return p


def leg_from_hip(p, s, direction, knee_bend=0., pole=(0, 0, 1)):
    """Place a leg from its hip along `direction`, with an optional knee bend (radians)."""
    hip = p.j['hip_'+s]
    d = unit(direction)
    if knee_bend < 1e-6:
        p.j['knee_'+s] = add(hip, mul(d, THIGH))
        ankle = add(hip, mul(d, THIGH+SHIN))
        p.j['ankle_'+s] = ankle
    else:
        knee = add(hip, mul(d, THIGH))
        axis = unit(cross(d, unit(pole)))
        shin = rotate(d, axis, knee_bend)
        p.j['knee_'+s] = knee
        ankle = add(knee, mul(shin, SHIN))
        p.j['ankle_'+s] = ankle
    p.foot(s, ankle=ankle, pitch=-radians(60), contact=False)
    return ankle


def sit_ups(name, phase):
    """S37: knees bent, hands behind the head, curl up toward the knees, lower with control."""
    t = pulse(phase)
    p = supine(Pose(name, phase))
    curl(p, radians(45)*t, radians(70)*t)
    set_head(p, pitch=radians(10)*t)
    hands_behind_head(p)
    feet_planted(p)
    p.contacts['feet'] = (.36, 0, 0)
    p.view = {'azimuth': 70, 'elevation': 18}  # user-approved (10/10); keep
    return p


def reverse_crunches(name, phase):
    """S38: arms at the sides, knees at 90 degrees; curl the knees toward the chest, lifting the hips."""
    t = pulse(phase)
    # The back and arms stay still on the floor; only the legs move (user note).
    p = supine(Pose(name, phase))
    arms_along_floor(p)
    for s in SIDES:
        thigh = rotate((0, 0, 1), (0, 1, 0), -radians(45)*t)
        leg_from_hip(p, s, thigh, knee_bend=radians(90), pole=(1, 0, 0))
    set_head(p)
    p.view = dict(SUPINE_VIEW)
    return p


def bicycle_crunches(name, phase):
    """S39: one knee drives in as the other leg extends; rotate the opposite elbow toward it; alternate."""
    side = 'l' if phase < .5 else 'r'
    local = (phase*2) % 1.
    t = pulse(local)
    p = supine(Pose(name, phase))
    curl(p, radians(12), radians(34))
    # Rotate the shoulders toward the driving knee.
    up = p.up
    turn = side_sign(side)*radians(24)*t
    for s in SIDES:
        p.j['shoulder_'+s] = add(p.j['chest'], rotate((0, side_sign(s)*SHOULDER_HALF, 0), up, turn))
    hands_behind_head(p)
    for s in SIDES:
        drive = t if s == side else 0.
        bent = rotate((0, 0, 1), (0, 1, 0), -radians(35)*drive)
        long = rotate((1, 0, 0), (0, 1, 0), -radians(25))
        d = unit(mix_point(long, bent, max(drive, .15)))
        leg_from_hip(p, s, d, knee_bend=radians(10+95*drive), pole=(1, 0, 0))
    p.view = {'azimuth': 55, 'elevation': 24}
    return p


def flutter_kicks(name, phase):
    """S40: head and shoulders slightly lifted, legs hover; small quick alternating kicks."""
    # Back flat on the mat, head down: reads unmistakably as lying face up (user note).
    p = supine(Pose(name, phase))
    arms_along_floor(p)
    for s in SIDES:
        kick = sin(2*pi*2*phase + (0 if s == 'l' else pi))
        d = rotate((1, 0, 0), (0, 1, 0), -radians(14+9*kick))
        leg_from_hip(p, s, d)
    p.view = dict(SUPINE_VIEW)
    return p


def leg_raises(name, phase):
    """S41: straight legs together rise to about 45 degrees and lower to hover above the floor."""
    t = pulse(phase)
    p = supine(Pose(name, phase))
    arms_along_floor(p)
    for s in SIDES:
        d = rotate((1, 0, 0), (0, 1, 0), -radians(8+37*t))
        leg_from_hip(p, s, d)
    p.view = dict(SUPINE_VIEW)
    return p


def prone(p, pelvis_x=-.02, lift=0., chest_lift=0.):
    """Face down, head toward -x; the person's left side is at -y."""
    p.torso((pelvis_x, 0, .10), up=(-1, 0, 0))
    lower = toward_head(radians(0))
    upper = toward_head(chest_lift)
    articulate(p, lower, upper)
    for s in SIDES:
        sg = side_sign(s)
        p.j['shoulder_'+s] = add(p.j['chest'], (0, -sg*SHOULDER_HALF, 0))
        p.j['hip_'+s] = add(p.j['pelvis'], (0, -sg*HIP_HALF, 0))
    p.forward = (0, 0, -1)
    p.j['face'] = add(p.j['head'], (0, 0, -.075))
    return p


def prone_legs(p, lift=0.):
    for s in SIDES:
        d = rotate((1, 0, 0), (0, 1, 0), -radians(12)*lift)
        hip = p.j['hip_'+s]
        p.j['knee_'+s] = add(hip, mul(d, THIGH))
        ankle = add(hip, mul(d, THIGH+SHIN))
        ankle = (ankle[0], ankle[1], max(ankle[2], .04))
        p.j['ankle_'+s] = ankle
        p.foot(s, ankle=ankle, pitch=radians(150), contact=False)
    return p


def superman(name, phase):
    """S56: face down; lift arms, chest and legs together, reach long; hold; lower."""
    t = ease_hold(phase)
    p = prone(Pose(name, phase), chest_lift=radians(16)*t)
    prone_legs(p, lift=t)
    for s in SIDES:
        shoulder = p.j['shoulder_'+s]
        reach = rotate((-1, 0, 0), (0, 1, 0), radians(18)*t)
        wrist = add(shoulder, add(mul(reach, .54), (0, -side_sign(s)*.04, 0)))
        wrist = (wrist[0], wrist[1], max(wrist[2], .05))
        p.arm(s, wrist, pole=add(shoulder, (0, 0, 1)))
    set_head(p, pitch=radians(6))
    p.j['face'] = add(p.j['head'], (0, 0, -.075))
    p.view = {'azimuth': 72, 'elevation': 14}
    return p


def back_lifts(name, phase):
    """Chart-defined: face down, hands by the temples; lift the chest, lower with control."""
    t = pulse(phase)
    p = prone(Pose(name, phase), chest_lift=radians(24)*t)
    prone_legs(p)
    for s in SIDES:
        sg = side_sign(s)
        wrist = add(p.j['head'], (.02, -sg*.09, -.02))
        p.arm(s, wrist, pole=add(p.j['shoulder_'+s], (-.2, -sg*.8, .2)))
    p.view = {'azimuth': 72, 'elevation': 14}
    return p


def high_plank(p, angle=TOP, hands=None):
    plank_body(p, angle)
    plant_hands(p, hands or {s: (.24, side_sign(s)*.225) for s in SIDES})
    return p


def alt_arm_leg_plank(name, phase):
    """Chart-defined: in a high plank, reach one arm forward and the opposite leg back; alternate."""
    side, local = two_reps(phase)
    t = hold_cycle(local, into=.3, hold=.3)
    p = Pose(name, phase)
    u, ankles = plank_body(p, TOP)
    leg = 'r' if side == 'l' else 'l'
    hip = p.j['hip_'+leg]
    d = rotate(mul(u, -1), (0, 1, 0), radians(22)*t)
    ankle = add(hip, mul(d, THIGH+SHIN))
    p.j['knee_'+leg] = add(hip, mul(d, THIGH))
    p.j['ankle_'+leg] = ankle
    p.foot(leg, ankle=ankle, pitch=radians(60), contact=t < 1e-6)
    for s in SIDES:
        sg = side_sign(s)
        planted = (.24, sg*.225, .05)
        if s == side and t > 0:
            reach = add(p.j['shoulder_'+s], (.54*cos(radians(10)), 0, .54*sin(radians(10))))
            wrist = mix_point(planted, reach, t)
            p.arm(s, wrist, pole=add(p.j['shoulder_'+s], (0, sg*.3, -.5)))
        else:
            p.arm(s, planted, pole=add(p.j['shoulder_'+s], (-.4, sg*.3, -.15)), palm=(.29, sg*.225, .014), contact=True)
    p.view = dict(PLANK_VIEW)
    return p


def shoulder_taps(name, phase):
    """S59: high plank, feet hip-width; lift one hand to tap the opposite shoulder; alternate."""
    side, local = two_reps(phase)
    t = hold_cycle(local, into=.35, hold=.2)
    p = Pose(name, phase)
    plank_body(p, TOP, foot_y=.16)
    for s in SIDES:
        sg = side_sign(s)
        planted = (.24, sg*.225, .05)
        if s == side and t > 0:
            other = p.j['shoulder_'+('r' if s == 'l' else 'l')]
            # Around, not through, the neck: under the chest, then onto the front of the other shoulder.
            under = add(p.j['chest'], (.06, 0, -.20))
            tap = add(other, (.07, sg*.03, -.03))
            path = mix_point(planted, under, stage(t, 0, .5)) if t < .5 else mix_point(under, tap, stage(t, .5, 1.))
            p.arm(s, path, pole=add(p.j['shoulder_'+s], (-.1, sg*.5, -.6)))
        else:
            p.arm(s, planted, pole=add(p.j['shoulder_'+s], (-.4, sg*.3, -.15)), palm=(.29, sg*.225, .014), contact=True)
    p.view = {'azimuth': 40, 'elevation': 28}
    return p


def climbers(name, phase):
    """S44: push-up position; drive the knees toward the chest alternately in a running rhythm."""
    p = Pose(name, phase)
    plank_body(p, TOP)
    for s in SIDES:
        drive = pulse((phase*2 + (0 if s == 'l' else .5)) % 1.)
        knee_drive(p, s, drive, (.30, side_sign(s)*.06, -.34), (1, 0, -.4))
    plant_hands(p, {s: (.24, side_sign(s)*.225) for s in SIDES})
    p.view = dict(PLANK_VIEW)
    return p


def plank_jump_ins(name, phase):
    """S45: from a plank, jump both feet in to a crouch under the hips, then jump back out."""
    t = hold_cycle(phase, into=.3, hold=.15)
    p = Pose(name, phase)
    hands = {s: (.24, side_sign(s)*.24) for s in SIDES}
    angle = TOP+radians(40)*t
    toe_x = -.99+.55*t
    airborne = sin(pi*stage(phase, 0, .30))*.5+sin(pi*stage(phase, .45, .75))*.5
    u, ankles = plank_body(p, TOP)
    # Crouch: feet land under the hips, knees tucked toward the chest.
    pelvis = mix_point(p.j['pelvis'], (-.30, 0, .42), t)
    lean = mix_point(u, unit((.95, 0, .30)), t)
    p.torso(add(pelvis, (0, 0, .04*airborne)), up=unit(lean))
    for s in SIDES:
        sg = side_sign(s)
        toe = (toe_x, sg*.13, .04*airborne)
        ankle = p.foot(s, toe=toe, pitch=radians(60), contact=airborne < 1e-3)
        p.leg(s, ankle, pole=add(p.j['hip_'+s], (1, sg*.2, -.2)))
    plant_hands(p, hands)
    p.view = dict(PLANK_VIEW)
    return p


def tricep_extensions(name, phase):
    """S51: from a forearm plank, press up to a straight-arm plank and lower back to the forearms."""
    t = pulse(phase)
    p = Pose(name, phase)
    reach = THIGH+SHIN+TORSO
    shoulder_z = .31+(.52-.31)*t
    ankle_z = ANKLE_HEIGHT+.02
    angle = asin_clamped((shoulder_z-ankle_z)/reach)
    plank_body(p, angle, toe_x=-1.02)
    for s in SIDES:
        sg = side_sign(s)
        wrist = (.30, sg*.20, .05)
        # Pole below and behind: the elbows fold down onto the floor at the bottom.
        p.arm(s, wrist, pole=add(p.j['shoulder_'+s], (-.3, sg*.05, -.6)), palm=(.35, sg*.20, .014), contact=True)
        if t < .15:
            p.contacts['elbow_'+s] = p.j['elbow_'+s]
    p.view = dict(PLANK_VIEW)
    return p

def pseudo_planche(name, phase):
    """Chart-defined: high plank with hands turned out beside the waist; lean the shoulders forward past the hands."""
    t = hold_cycle(phase, into=.35, hold=.30)
    p = Pose(name, phase)
    plank_body(p, TOP-radians(7), toe_x=-1.+.14*t)
    for s in SIDES:
        sg = side_sign(s)
        wrist = (.06, sg*.24, .05)
        p.arm(s, wrist, pole=add(p.j['shoulder_'+s], (-.4, sg*.3, -.1)), palm=(.06, sg*.29, .014), contact=True)
    p.view = dict(PLANK_VIEW)
    return p


def tricep_dips(name, phase):
    """S50: seated, hands behind with fingers toward the feet, hips up; bend the elbows straight back and press."""
    t = pulse(phase)
    p = Pose(name, phase)
    pelvis = (-.10, 0, .24-.10*t)
    p.torso(pelvis, lean=-radians(35))
    for s in SIDES:
        sg = side_sign(s)
        ankle = p.foot(s, ankle=(.42, sg*.14, ANKLE_HEIGHT))
        p.leg(s, ankle, pole=add(p.j['hip_'+s], (0, 0, 1)))
        wrist = (-.40, sg*.20, .05)
        p.arm(s, wrist, pole=add(p.j['shoulder_'+s], (-.6, sg*.1, .1)), palm=(-.35, sg*.20, .014), contact=True)
    p.view = {'azimuth': 72, 'elevation': 10}
    return p


FLOOR_MOTIONS = {
    'sit-ups': sit_ups,
    'reverse-crunches': reverse_crunches,
    'bicycle-crunches': bicycle_crunches,
    'flutter-kicks': flutter_kicks,
    'leg-raises': leg_raises,
    'superman': superman,
    'back-lifts': back_lifts,
    'alt-arm-leg-plank': alt_arm_leg_plank,
    'shoulder-taps': shoulder_taps,
    'climbers': climbers,
    'plank-jump-ins': plank_jump_ins,
    'tricep-extensions': tricep_extensions,
    'pseudo-planche': pseudo_planche,
    'tricep-dips': tricep_dips,
}
