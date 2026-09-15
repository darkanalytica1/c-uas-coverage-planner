"""Load and save scenarios as JSON, so a site is reviewable, versionable data."""
from __future__ import annotations

import json

from .model import Obstacle, Scenario, Sensor


def load(path: str) -> Scenario:
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    sensors = [Sensor(**s) for s in d.get("sensors", [])]
    obstacles = [
        Obstacle(o["name"], tuple(tuple(v) for v in o["vertices"]))
        for o in d.get("obstacles", [])
    ]
    return Scenario(
        name=d.get("name", "scenario"),
        width_m=d["width_m"], height_m=d["height_m"],
        resolution_m=d.get("resolution_m", 25.0),
        sensors=sensors, obstacles=obstacles,
    )


def dump(scenario: Scenario, path: str) -> None:
    d = {
        "name": scenario.name, "width_m": scenario.width_m,
        "height_m": scenario.height_m, "resolution_m": scenario.resolution_m,
        "sensors": [vars(s) for s in scenario.sensors],
        "obstacles": [{"name": o.name, "vertices": [list(v) for v in o.vertices]}
                      for o in scenario.obstacles],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)
