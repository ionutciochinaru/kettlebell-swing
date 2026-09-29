"""App icon, Android adaptive layers, splash image and favicon.

python3 tools/make_icons.py

The watch renderer draws the figure at the top of a two-hand swing; an orange
arc behind it traces the bell's path through the whole swing. Pillow only.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/animation'))
import render  # noqa: E402
from motions import pose_for  # noqa: E402

ACCENT = (255, 107, 43)
BG = (0, 0, 0)
OUT = ROOT / 'assets/images'


def figure_layers(size, margin):
    """(figure RGBA, arc RGBA) rendered at `size`, figure fitted inside `margin`."""
    render.WIDTH = render.HEIGHT = size
    poses = [pose_for('kb-swing', i / 64) for i in range(64)]
    camera = render.Camera(poses, {'azimuth': 78, 'elevation': 8})
    camera.ground = None
    # Refit: scale the figure into the requested margin, centred.
    camera.scale *= margin
    frame = render.draw_frame(pose_for('kb-swing', .5), camera)

    # Opaque where the figure or its black outline is: dilate the non-black area.
    luminance = frame.convert('L').point(lambda v: 255 if v > 14 else 0)
    mask = luminance.filter(ImageFilter.MaxFilter(7))
    figure = frame.convert('RGBA')
    figure.putalpha(mask)

    arc = Image.new('RGBA', (size*4, size*4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(arc)
    points = []
    for i in range(33):
        # Half a cycle: from the backswing up to the chest-height float.
        bell = pose_for('kb-swing', .5*i/32)['props'][0]['center']
        x, y = camera.point(bell)
        points.append((x, y))
    draw.line(points, fill=ACCENT + (255,), width=int(size*.055*4), joint='curve')
    for x, y in (points[0], points[-1]):
        r = size*.055*2
        draw.ellipse((x-r, y-r, x+r, y+r), fill=ACCENT + (255,))
    arc = arc.resize((size, size), Image.Resampling.LANCZOS)
    return figure, arc


def compose(size, margin, background=BG):
    figure, arc = figure_layers(size, margin)
    canvas = Image.new('RGBA', (size, size), background + (255,) if background else (0, 0, 0, 0))
    canvas.alpha_composite(arc)
    canvas.alpha_composite(figure)
    return canvas


def main():
    icon = compose(1024, .78)
    icon.convert('RGB').save(OUT / 'icon.png')
    # Adaptive icon: content inside the central ~66% safe zone.
    compose(1024, .56, background=None).save(OUT / 'android-icon-foreground.png')
    Image.new('RGB', (1024, 1024), BG).save(OUT / 'android-icon-background.png')
    fg = compose(1024, .56, background=None)
    white = Image.new('RGBA', fg.size, (255, 255, 255, 255))
    white.putalpha(fg.getchannel('A'))
    white.save(OUT / 'android-icon-monochrome.png')
    compose(1024, .9, background=None).save(OUT / 'splash-icon.png')
    icon.convert('RGB').resize((48, 48), Image.Resampling.LANCZOS).save(OUT / 'favicon.png')
    print('icons written to', OUT)


if __name__ == '__main__':
    main()
