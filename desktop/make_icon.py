# -*- coding: utf-8 -*-
"""生成应用图标 assets/app.ico（简洁齿轮 + 深蓝底，贴合企业工具气质）。"""

import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'assets', 'app.ico')

BG = (21, 73, 154, 255)   # #15499A
FG = (255, 255, 255, 255)


def render(size):
    s = size
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.21), fill=BG)

    cx = cy = s / 2.0
    r_out = s * 0.315
    r_in = s * 0.235
    teeth = 10
    pts = []
    for i in range(teeth * 2):
        ang = math.pi * 2 * i / (teeth * 2) - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=FG)

    r_hole = s * 0.095
    d.ellipse([cx - r_hole, cy - r_hole, cx + r_hole, cy + r_hole], fill=BG)
    return img


def main():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [render(x) for x in sizes]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    imgs[-1].save(OUT, format='ICO', sizes=[(x, x) for x in sizes])
    print('图标已生成 ->', OUT)


if __name__ == '__main__':
    main()
