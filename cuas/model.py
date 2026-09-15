"""Scenario model: sensors, obstacles, and the site they sit in.

Coordinates are metres in a local plane. The x axis points east, the y axis
points north, so a compass bearing of 0 is +y (north) and 90 is +x (east).
Angles are compass degrees throughout, because that is how sensor sectors are
actually described.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Sensor:
    """A detection sensor with a range and a field of view.

    A cell is detected by this sensor when it lies within [min_range, range],
    inside the field-of-view sector, and has clear line of sight (not masked by
    an obstacle). ``fov_width_deg`` of 360 means an omnidirectional sensor and
    the centre is then irrelevant.
    """

    name: str
    x: float
    y: float
    range_m: float
    kind: str = "radar"          # radar | rf | eo | acoustic (label only)
    fov_center_deg: float = 0.0  # compass bearing the sector is centred on
    fov_width_deg: float = 360.0
    min_range_m: float = 0.0

    def __post_init__(self) -> None:
        if self.range_m <= 0:
            raise ValueError(f"sensor {self.name}: range must be positive")
        if not 0 < self.fov_width_deg <= 360:
            raise ValueError(f"sensor {self.name}: fov_width must be in (0, 360]")
        if self.min_range_m < 0 or self.min_range_m >= self.range_m:
            raise ValueError(f"sensor {self.name}: min_range must be in [0, range)")

    @property
    def omnidirectional(self) -> bool:
        return self.fov_width_deg >= 360.0


@dataclass(frozen=True)
class Obstacle:
    """A building or terrain block, as a closed polygon of (x, y) vertices.

    It does two things: cells inside it cannot be covered, and it masks line of
    sight, so a sensor cannot see cells in the shadow behind it.
    """

    name: str
    vertices: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if len(self.vertices) < 3:
            raise ValueError(f"obstacle {self.name}: need at least 3 vertices")

    def edges(self):
        v = self.vertices
        return [(v[i], v[(i + 1) % len(v)]) for i in range(len(v))]


@dataclass
class Scenario:
    """A site of a given size and resolution, with sensors and obstacles."""

    name: str
    width_m: float
    height_m: float
    resolution_m: float = 25.0
    sensors: list[Sensor] = field(default_factory=list)
    obstacles: list[Obstacle] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.width_m <= 0 or self.height_m <= 0 or self.resolution_m <= 0:
            raise ValueError("width, height and resolution must be positive")

    @property
    def nx(self) -> int:
        return max(1, int(round(self.width_m / self.resolution_m)))

    @property
    def ny(self) -> int:
        return max(1, int(round(self.height_m / self.resolution_m)))
