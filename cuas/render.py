"""Render a coverage result to a PNG map: coverage shading, sensors, dead zones."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .coverage import CoverageResult

# Palette: light, restrained. The dead zone is the one thing to notice, so it
# alone carries the accent colour; coverage levels are graded navy tints.
BG = (245, 247, 250)        # page #F5F7FA
INK = (14, 23, 38)          # ink #0E1726
MUTED = (61, 74, 92)         # ink-2 #3D4A5C
FRAME = (216, 222, 230)     # line #D8DEE6
OBSTACLE = (61, 74, 92)
# coverage level -> colour
DEAD = (214, 196, 150)      # brass #8A6A1F at ~40%
L1 = (225, 231, 239)        # navy #0B2545 tints
L2 = (172, 184, 199)
L3 = (109, 124, 143)
SENSOR = (11, 37, 69)       # navy #0B2545
RANGE_RING = (11, 37, 69)


def _font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/System/Library/Fonts/Menlo.ttc",
              "C:/Windows/Fonts/consola.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _level_colour(count):
    return {0: DEAD, 1: L1, 2: L2}.get(int(count), L3)


def render(result: CoverageResult, path: str, target_px: int = 820) -> str:
    r = result
    sc = r.scenario
    ny, nx = r.coverage_count.shape
    cell = max(3, round(target_px / nx))
    map_w, map_h = nx * cell, ny * cell
    margin, title_h, legend_w = 24, 52, 210

    # base raster from coverage levels
    rgb = np.zeros((ny, nx, 3), dtype=np.uint8)
    for lvl in range(0, int(r.coverage_count.max()) + 1):
        rgb[(r.coverage_count == lvl) & r.buildable] = _level_colour(lvl)
    rgb[~r.buildable] = OBSTACLE
    base = Image.fromarray(rgb, "RGB").resize((map_w, map_h), Image.NEAREST)
    base = base.transpose(Image.FLIP_TOP_BOTTOM)  # north up

    W = margin * 2 + map_w + legend_w
    H = margin * 2 + title_h + map_h
    img = Image.new("RGB", (W, H), BG)
    img.paste(base, (margin, margin + title_h))
    d = ImageDraw.Draw(img, "RGBA")
    fb, fs, ft = _font(13), _font(11), _font(18)

    def to_px(x, y):
        return (margin + x / sc.resolution_m * cell,
                margin + title_h + map_h - y / sc.resolution_m * cell)

    # title
    d.text((margin, margin + 6), sc.name, font=ft, fill=INK)
    d.text((margin, margin + 30), f"{sc.width_m:.0f} x {sc.height_m:.0f} m  ."
           f"  {len(sc.sensors)} sensors  .  {sc.resolution_m:.0f} m grid",
           font=fs, fill=MUTED)

    # rings and wedges go on their own layer, clipped to the map frame
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # obstacles outline + label
    for obs in sc.obstacles:
        pts = [to_px(*v) for v in obs.vertices]
        d.polygon(pts, outline=INK, width=1)

    # sensors: range ring, FOV wedge, marker, label
    for s in sc.sensors:
        cx, cy = to_px(s.x, s.y)
        rr = s.range_m / sc.resolution_m * cell
        od.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=RANGE_RING + (150,), width=1)
        if not s.omnidirectional:
            # wedge: compass bearing to screen angle (0=N up, clockwise)
            a0 = s.fov_center_deg - s.fov_width_deg / 2
            a1 = s.fov_center_deg + s.fov_width_deg / 2
            poly = [(cx, cy)]
            steps = max(2, int(s.fov_width_deg / 5))
            for k in range(steps + 1):
                ang = math.radians(a0 + (a1 - a0) * k / steps)
                poly.append((cx + rr * math.sin(ang), cy - rr * math.cos(ang)))
            od.polygon(poly, outline=RANGE_RING + (200,))

    clip = Image.new("L", (W, H), 0)
    ImageDraw.Draw(clip).rectangle([margin, margin + title_h, margin + map_w, margin + title_h + map_h], fill=255)
    overlay.putalpha(Image.composite(overlay.getchannel("A"), clip, clip))
    img.paste(overlay, (0, 0), overlay)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([margin, margin + title_h, margin + map_w, margin + title_h + map_h],
                outline=FRAME, width=1)

    for s in sc.sensors:
        cx, cy = to_px(s.x, s.y)
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=SENSOR, outline=(255, 255, 255))
        d.text((cx + 8, cy - 16), f"{s.name}", font=fb, fill=INK)
        d.text((cx + 8, cy), f"{s.kind} {s.range_m:.0f}m", font=fs, fill=MUTED)

    # legend
    lx = margin + map_w + 20
    ly = margin + title_h
    d.text((lx, ly), "COVERAGE", font=fb, fill=INK)
    items = [("Dead zone (0)", DEAD), ("Single (1x)", L1), ("Double (2x)", L2),
             ("Triple+ (3x)", L3), ("Obstacle", OBSTACLE)]
    for i, (label, col) in enumerate(items):
        yy = ly + 26 + i * 24
        d.rectangle([lx, yy, lx + 16, yy + 16], fill=col, outline=FRAME)
        d.text((lx + 24, yy + 1), label, font=fs, fill=MUTED)
    # north arrow
    ny_ = ly + 26 + len(items) * 24 + 20
    d.line([lx + 8, ny_ + 26, lx + 8, ny_], fill=INK, width=2)
    d.polygon([(lx + 8, ny_ - 2), (lx + 4, ny_ + 6), (lx + 12, ny_ + 6)], fill=INK)
    d.text((lx + 18, ny_), "N", font=fb, fill=INK)

    img.save(path)
    return path
