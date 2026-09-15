# C-UAS Sensor Coverage Planner

Model a site, place counter-drone sensors, and see where you are actually covered, where coverage overlaps, and where the dead zones are that a low, slow drone could exploit. It accounts for range, field of view, and, importantly, the line-of-sight shadows cast by buildings and terrain.

![Example coverage map](examples/example-coverage.png)

## Why this exists

A single sensor ring looks like protection and is not. The earth's curvature, buildings and terrain leave gaps, and layered defence exists precisely to cover them. The hard, invisible part of counter-drone site design is not the datasheet range of a sensor: it is where the overlapping coverage actually lands once the real site gets in the way. This tool makes that visible, and turns "we have three sensors" into "we have a 436,000 square metre dead zone on the eastern approach."

## The model

The site is a grid. A cell is detected by a sensor when it meets three conditions:

1. **Range.** It lies within the sensor's minimum and maximum range. A minimum range models the blind cone directly over some sensors.
2. **Field of view.** It falls inside the sensor's sector, given as a compass centre bearing and a width. A width of 360 degrees is an omnidirectional sensor.
3. **Line of sight.** The straight line from the sensor to the cell is not crossed by an obstacle. This is the part that separates a real coverage estimate from drawing circles: a building or ridge casts a shadow, and cells in that shadow are dead even though they are well within range.

Coverage is then the number of sensors that detect each cell. Zero is a dead zone; one is single coverage; two or more is redundant, layered coverage.

## What you get

```
coverage        : 56.6% of open ground
dead zones      : 43.4%
max overlap     : 2 sensors
redundancy      :
    dead       : 43.4%
      1x       : 37.8%
      2x       : 18.9%
worst dead zone : 436,275 m^2 around (1343, 721)
```

Plus the rendered map above: dead zones in red, single coverage amber, overlap in green, obstacles in slate, and each sensor with its range ring and field-of-view wedge.

## Use it

A site is a JSON file, so it is reviewable, diffable and versionable:

```json
{
  "name": "Example site",
  "width_m": 1600, "height_m": 1200, "resolution_m": 15,
  "sensors": [
    {"name": "RAD-1", "kind": "radar", "x": 800, "y": 600, "range_m": 650},
    {"name": "RF-N", "kind": "rf", "x": 400, "y": 1000, "range_m": 500,
     "fov_center_deg": 45, "fov_width_deg": 140}
  ],
  "obstacles": [
    {"name": "hangar", "vertices": [[650,700],[950,700],[950,900],[650,900]]}
  ]
}
```

```bash
python -m cuas plan examples/example.json --out map.png
```

Or from Python:

```python
from cuas import Sensor, Scenario, compute
from cuas.stats import summarise

sc = Scenario("site", 1000, 1000, resolution_m=10,
              sensors=[Sensor("R1", 500, 500, 400, "radar"),
                       Sensor("RF", 200, 200, 350, "rf", fov_center_deg=45, fov_width_deg=120)])
print(summarise(compute(sc)).as_text())
```

## Scope and honesty

This is a **planning aid**, not a propagation or radar-performance model. It works in a two-dimensional top-down plane with hard coverage (a cell is covered or not), and it treats obstacles as line-of-sight blockers. That is deliberately simple: it answers the geometry question, where do rings and sectors overlap once obstacles get in the way, which is the question most site layouts get wrong. It does not model detection probability against a given target, multipath, elevation, or the drone's own altitude, and it is not a substitute for a real siting study. The code says where each assumption stops.

## Install and run

```bash
git clone https://github.com/darkanalytica1/c-uas-coverage-planner
cd c-uas-coverage-planner
pip install numpy pillow
python -m pytest tests -q          # 11 tests
python -m cuas plan examples/example.json --out map.png
```

Python 3.10+. Depends on numpy and Pillow.

## Licence

MIT. See [LICENSE](LICENSE).
