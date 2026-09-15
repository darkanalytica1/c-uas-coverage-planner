"""Summary statistics for a coverage result, including the worst dead zone."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from .coverage import CoverageResult


@dataclass
class CoverageStats:
    buildable_cells: int
    covered_pct: float
    dead_pct: float
    redundancy: dict          # overlap level -> percent of buildable area
    max_overlap: int
    largest_dead_zone_m2: float
    largest_dead_zone_centre: tuple[float, float] | None

    def as_text(self) -> str:
        lines = [
            f"coverage        : {self.covered_pct:.1f}% of open ground",
            f"dead zones      : {self.dead_pct:.1f}%",
            f"max overlap     : {self.max_overlap} sensors",
            "redundancy      :",
        ]
        for level in sorted(self.redundancy):
            tag = "dead" if level == 0 else f"{level}x"
            lines.append(f"    {tag:>4}       : {self.redundancy[level]:.1f}%")
        if self.largest_dead_zone_centre:
            cx, cy = self.largest_dead_zone_centre
            lines.append(
                f"worst dead zone : {self.largest_dead_zone_m2:,.0f} m^2 "
                f"around ({cx:.0f}, {cy:.0f})"
            )
        return "\n".join(lines)


def _largest_component(mask: np.ndarray, res: float):
    """Return (area_m2, (cx, cy)) of the largest connected True region."""
    if not mask.any():
        return 0.0, None
    visited = np.zeros_like(mask)
    ny, nx = mask.shape
    best_cells, best_centroid = 0, None
    for sy in range(ny):
        for sx in range(nx):
            if mask[sy, sx] and not visited[sy, sx]:
                q = deque([(sy, sx)])
                visited[sy, sx] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny2, nx2 = y + dy, x + dx
                        if 0 <= ny2 < ny and 0 <= nx2 < nx and mask[ny2, nx2] and not visited[ny2, nx2]:
                            visited[ny2, nx2] = True
                            q.append((ny2, nx2))
                if len(cells) > best_cells:
                    best_cells = len(cells)
                    ys = np.mean([c[0] for c in cells])
                    xs = np.mean([c[1] for c in cells])
                    best_centroid = ((xs + 0.5) * res, (ys + 0.5) * res)
    return best_cells * res * res, best_centroid


def summarise(result: CoverageResult) -> CoverageStats:
    r = result
    total = int(r.buildable.sum())
    area_cell = r.scenario.resolution_m ** 2
    max_overlap = int(r.coverage_count[r.buildable].max()) if total else 0
    redundancy = {}
    for level in range(0, max_overlap + 1):
        cells = int(((r.coverage_count == level) & r.buildable).sum())
        redundancy[level] = 100.0 * cells / total if total else 0.0
    dz_area, dz_centre = _largest_component(r.dead_zone, r.scenario.resolution_m)
    return CoverageStats(
        buildable_cells=total,
        covered_pct=100.0 * int(r.covered[r.buildable].sum()) / total if total else 0.0,
        dead_pct=100.0 * int(r.dead_zone.sum()) / total if total else 0.0,
        redundancy=redundancy,
        max_overlap=max_overlap,
        largest_dead_zone_m2=dz_area,
        largest_dead_zone_centre=dz_centre,
    )
