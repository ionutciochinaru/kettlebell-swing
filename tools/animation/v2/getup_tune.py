"""Search get-up key poses that are reachable and balanced (offline helper).

python3 tools/animation/v2/getup_tune.py

For each stage it samples trunk orientation (and pelvis / thigh where free),
builds the held pose with the real v2 builders, and scores: exact contact
reach, whole-body + bell COM margin inside that stage's support, and joint
clearances. Prints the best parameters to paste into getup.py.
"""
import random
import sys
from math import sin, cos, radians
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v2 import getup as g  # noqa: E402
from v2 import body, collide  # noqa: E402
from rig import unit, norm, sub  # noqa: E402

random.seed(7)


def direction(az, el):
    return unit((cos(el) * cos(az), cos(el) * sin(az), sin(el)))


def score(params, without=()):
    state = {'a': params, 'b': params, 'u': 0.}
    p = g._build('t', 0., state, 0., 0.).result()
    if p['qa']['ik_errors']:
        return -1e3, None
    for name in without:
        p['contacts'].pop(name, None)
    hull = body.convex_hull(body.support_points(p))
    com = body.centre_of_mass(p)[0]
    m = body.margin((com[0], com[1]), hull)
    clear = min(v for k, v in collide.clearances(p).items())
    low = min(v[2] for k, v in p['joints'].items() if k != 'face')
    s = min(m, .08) * 10 + min(clear, .02) * 5 + min(low, 0.) * 20
    return s, (round(m, 3), round(clear, 3), round(low, 3))


def search(name, template, sample, n=2500, without=()):
    best = (-1e9, None, None)
    for _ in range(n):
        params = dict(template, **sample())
        s, info = score(params, without)
        if s > best[0]:
            best = (s, params, info)
    print(name, 'score', round(best[0], 3), 'margin/clearance/low', best[2])
    print('   ', {k: (tuple(round(x, 3) for x in v) if isinstance(v, tuple) else round(v, 3) if isinstance(v, float) else v)
                   for k, v in best[1].items() if k in ('pelvis', 'up', 'twist', 'thigh', 'shin')})
    RESULTS[name.split()[0]] = best[1]
    return best[1]


RESULTS = {}


def tune_push():
    search('push (balanced without the hand)', dict(g.PUSH[1]), lambda: {
        'thigh': direction(radians(random.uniform(-30, 60)), radians(random.uniform(65, 89))),
        'up': direction(radians(random.uniform(-120, 30)), radians(random.uniform(40, 80))),
        'twist': radians(random.uniform(-25, 5))}, n=6000, without=('palm_r',))

if __name__ == '__main__':
    lie = dict(g.LIE[1])
    elbow = search('elbow', dict(g.ELB[1]), lambda: {
        'up': direction(radians(random.uniform(185, 250)), radians(random.uniform(15, 60))),
        'twist': radians(random.uniform(-40, 0))})
    post = search('post', dict(g.POST[1]), lambda: {
        'up': direction(radians(random.uniform(185, 250)), radians(random.uniform(30, 75))),
        'twist': radians(random.uniform(-30, 5))})
    bridge = search('bridge', dict(g.BRIDGE[1]), lambda: {
        'pelvis': (random.uniform(-.05, .2), random.uniform(-.15, .05), random.uniform(.3, .5)),
        'up': direction(radians(random.uniform(185, 260)), radians(random.uniform(10, 50))),
        'twist': radians(random.uniform(-30, 5))})
    sweep = search('sweep', dict(g.SWEEP[1]), lambda: {
        'thigh': direction(radians(random.uniform(-40, 60)), radians(random.uniform(55, 88))),
        'up': direction(radians(random.uniform(200, 280)), radians(random.uniform(20, 60))),
        'twist': radians(random.uniform(-20, 5))})
    kneel = search('kneel', dict(g.KNEEL[1]), lambda: {
        'thigh': direction(radians(random.uniform(-30, 60)), radians(random.uniform(70, 90))),
        'up': direction(radians(random.uniform(-40, 40)), radians(random.uniform(78, 90)))})
    tune_push()
    top = search('top', dict(g.TOP[1]), lambda: {
        'pelvis': (random.uniform(0., .16), random.uniform(-.08, .1), random.uniform(.74, .83)),
        'up': direction(radians(random.uniform(-40, 40)), radians(random.uniform(78, 90)))})

    import json
    Path(__file__).with_name('getup_tuned.json').write_text(json.dumps(
        {k: {p: v for p, v in d.items() if p in ('pelvis', 'up', 'twist', 'thigh', 'shin')} for k, d in RESULTS.items()}, indent=1))
    print('saved getup_tuned.json')
