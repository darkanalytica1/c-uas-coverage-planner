"""C-UAS sensor coverage planner.

Model a site, place detection sensors (radar, RF, electro-optical, acoustic)
with a range and a field of view, account for terrain and buildings that mask
line of sight, and compute where the site is covered, where coverage overlaps,
and where the dead zones are that a low, slow drone could exploit.

The point of the tool is the dead zone. A single sensor ring looks like
protection and is not: the earth's curvature, buildings and terrain leave gaps,
and layered defence exists to cover them. This planner makes those gaps visible.
"""
from .model import Obstacle, Scenario, Sensor  # noqa: F401
from .coverage import CoverageResult, compute  # noqa: F401

__version__ = "1.0.0"
__all__ = ["Sensor", "Obstacle", "Scenario", "compute", "CoverageResult"]
