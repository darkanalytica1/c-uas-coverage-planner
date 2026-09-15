import numpy as np
import pytest
from cuas import geometry as g
from cuas.model import Obstacle


def test_compass_bearing():
    assert float(g.compass_bearing(np.array(0.0), np.array(1.0))) == pytest.approx(0)    # north
    assert float(g.compass_bearing(np.array(1.0), np.array(0.0))) == pytest.approx(90)   # east
    assert float(g.compass_bearing(np.array(0.0), np.array(-1.0))) == pytest.approx(180) # south


def test_in_sector_wraps():
    b = np.array([350.0, 10.0, 90.0])
    m = g.in_sector(b, centre_deg=0.0, width_deg=40.0)
    assert list(m) == [True, True, False]


def test_omni_sector_all_true():
    b = np.array([0.0, 123.0, 359.0])
    assert g.in_sector(b, 0, 360).all()


def test_line_of_sight_blocks_behind_wall():
    X, Y = g.grid_centres(20, 20, 10.0)          # 200x200 m
    wall = Obstacle("w", ((90, 90), (110, 90), (110, 110), (90, 110)))
    los = g.line_of_sight_mask(100, 20, X, Y, [wall])   # sensor south of wall
    # a cell due north, behind the wall, must be masked
    assert not los[int(150 / 10), int(100 / 10)]
    # a cell south of the sensor (in front) is clear
    assert los[int(10 / 10), int(100 / 10)]
