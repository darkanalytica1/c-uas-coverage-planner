"""Render a coverage result to a PNG map: coverage shading, sensors, dead zones."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .coverage import CoverageResult

BG = (244, 245, 247)
INK = (20, 27, 38)
MUTED = (92, 102, 117)
OBSTACLE = (74, 82, 96)
# coverage level -> colour
DEAD = (211, 84, 70)
L1 = (222, 168, 84)
L2 = (108, 184, 112)
L3 = (56, 150, 120)
SENSOR = (34, 40, 54)
RANGE_RING = (47, 75, 122)


def _font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
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

    # map frame
    d.rectangle([margin, margin + title_h, margin + map_w, margin + title_h + map_h],
                outline=(205, 210, 218), width=1)

    # obstacles outline + label
    for obs in sc.obstacles:
        pts = [to_px(*v) for v in obs.vertices]
        d.polygon(pts, outline=(150, 158, 172), width=2)

    # sensors: range ring, FOV wedge, marker, label
    for s in sc.sensors:
        cx, cy = to_px(s.x, s.y)
        rr = s.range_m / sc.resolution_m * cell
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=RANGE_RING + (150,), width=1)
        if not s.omnidirectional:
            # wedge: compass bearing to screen angle (0=N up, clockwise)
            a0 = s.fov_center_deg - s.fov_width_deg / 2
            a1 = s.fov_center_deg + s.fov_width_deg / 2
            poly = [(cx, cy)]
            steps = max(2, int(s.fov_width_deg / 5))
            for k in range(steps + 1):
                ang = math.radians(a0 + (a1 - a0) * k / steps)
                poly.append((cx + rr * math.sin(ang), cy - rr * math.cos(ang)))
            d.polygon(poly, outline=RANGE_RING + (200,))
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
        d.rectangle([lx, yy, lx + 16, yy + 16], fill=col, outline=(200, 205, 214))
        d.text((lx + 24, yy + 1), label, font=fs, fill=MUTED)
    # north arrow
    ny_ = ly + 26 + len(items) * 24 + 20
    d.line([lx + 8, ny_ + 26, lx + 8, ny_], fill=INK, width=2)
    d.polygon([(lx + 8, ny_ - 2), (lx + 4, ny_ + 6), (lx + 12, ny_ + 6)], fill=INK)
    d.text((lx + 18, ny_), "N", font=fb, fill=INK)

    img.save(path)
    return path
