import pytest
from cuas import Sensor, Obstacle, Scenario
from cuas import scenario_io


def test_sensor_validation():
    with pytest.raises(ValueError):
        Sensor("x", 0, 0, -1)
    with pytest.raises(ValueError):
        Sensor("x", 0, 0, 100, fov_width_deg=0)
    with pytest.raises(ValueError):
        Sensor("x", 0, 0, 100, min_range_m=100)


def test_scenario_roundtrip(tmp_path):
    sc = Scenario("t", 800, 600, 20.0,
                  sensors=[Sensor("S", 100, 100, 300, "rf", 45, 120, 10)],
                  obstacles=[Obstacle("b", ((10, 10), (30, 10), (30, 30)))])
    p = tmp_path / "s.json"
    scenario_io.dump(sc, str(p))
    back = scenario_io.load(str(p))
    assert back.name == "t" and back.nx == sc.nx
    assert back.sensors[0].fov_width_deg == 120
    assert back.obstacles[0].vertices[0] == (10, 10)
