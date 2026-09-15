"""Compute where a site is covered, where coverage overlaps, and dead zones."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import geometry as geo
from .model import Scenario, Sensor


def sensor_mask(sensor: Sensor, X, Y, obstacles) -> np.ndarray:
    """Boolean grid: cells this one sensor detects.

    A cell is detected when it is within [min_range, range], inside the field
    of view, and has clear line of sight to the sensor.
    """
    dx = X - sensor.x
    dy = Y - sensor.y
    dist = np.hypot(dx, dy)
    m = (dist <= sensor.range_m) & (dist >= sensor.min_range_m)
    if not sensor.omnidirectional:
        bearing = geo.compass_bearing(dx, dy)
        m &= geo.in_sector(bearing, sensor.fov_center_deg, sensor.fov_width_deg)
    if obstacles:
        m &= geo.line_of_sight_mask(sensor.x, sensor.y, X, Y, obstacles)
    return m


@dataclass
class CoverageResult:
    """The computed coverage of a scenario."""

    scenario: Scenario
    coverage_count: np.ndarray          # (ny, nx) int: sensors covering each cell
    buildable: np.ndarray               # (ny, nx) bool: cell is open ground (not inside an obstacle)
    per_sensor: dict                    # name -> boolean mask

    @property
    def dead_zone(self) -> np.ndarray:
        """Open cells covered by no sensor."""
        return self.buildable & (self.coverage_count == 0)

    @property
    def covered(self) -> np.ndarray:
        return self.coverage_count > 0


def compute(scenario: Scenario) -> CoverageResult:
    """Run the coverage computation for a scenario."""
    X, Y = geo.grid_centres(scenario.nx, scenario.ny, scenario.resolution_m)

    inside_obstacle = np.zeros(X.shape, dtype=bool)
    for obs in scenario.obstacles:
        inside_obstacle |= geo.point_in_polygon(X, Y, obs.vertices)
    buildable = ~inside_obstacle

    count = np.zeros(X.shape, dtype=np.int16)
    per_sensor = {}
    for s in scenario.sensors:
        m = sensor_mask(s, X, Y, scenario.obstacles) & buildable
        per_sensor[s.name] = m
        count += m.astype(np.int16)

    return CoverageResult(scenario, count, buildable, per_sensor)
