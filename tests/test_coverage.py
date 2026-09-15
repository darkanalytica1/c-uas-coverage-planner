import pytest
from cuas import Sensor, Obstacle, Scenario, compute
from cuas.stats import summarise


def test_omni_range_only():
    sc = Scenario("t", 400, 400, 10.0, sensors=[Sensor("S", 200, 200, 100)])
    r = compute(sc)
    # cell at centre covered, cell far corner not
    assert r.per_sensor["S"][20, 20]
    assert not r.per_sensor["S"][0, 0]


def test_min_range_hole():
    sc = Scenario("t", 400, 400, 10.0, sensors=[Sensor("S", 200, 200, 150, min_range_m=60)])
    r = compute(sc)
    assert not r.per_sensor["S"][20, 20]      # too close, inside min range
    assert r.per_sensor["S"][20, 30]          # ~100 m out, covered


def test_sector_limits_coverage():
    north = Sensor("N", 200, 200, 150, fov_center_deg=0, fov_width_deg=60)
    sc = Scenario("t", 400, 400, 10.0, sensors=[north])
    r = compute(sc)
    assert r.per_sensor["N"][30, 20]          # due north, covered
    assert not r.per_sensor["N"][10, 20]      # due south, outside sector


def test_obstacle_creates_dead_zone_and_overlap():
    sc = Scenario("t", 1000, 1000, 10.0,
                  sensors=[Sensor("A", 300, 500, 400), Sensor("B", 700, 500, 400)])
    r = compute(sc)
    s = summarise(r)
    assert s.max_overlap == 2                 # the two ranges overlap in the middle
    assert s.covered_pct > 0 and s.dead_pct > 0
    assert abs(sum(s.redundancy.values()) - 100.0) < 0.5


def test_cell_inside_obstacle_not_covered():
    sc = Scenario("t", 400, 400, 10.0,
                  sensors=[Sensor("S", 50, 50, 500)],
                  obstacles=[Obstacle("b", ((180, 180), (220, 180), (220, 220), (180, 220)))])
    r = compute(sc)
    assert not r.buildable[20, 20]            # cell at (200,200) is inside the building
    assert not r.covered[20, 20]
