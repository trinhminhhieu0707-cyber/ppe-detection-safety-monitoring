import pytest
from src.common.types import BoundingBox

def test_bounding_box_properties():
    box = BoundingBox(x1=100.0, y1=50.0, x2=200.0, y2=250.0)
    assert box.width == 100.0
    assert box.height == 200.0
    assert box.area == 20000.0
    assert box.center == (150.0, 150.0)
    assert box.to_xyxy() == (100, 50, 200, 250)

def test_bounding_box_normalized():
    box = BoundingBox(x1=320.0, y1=240.0, x2=640.0, y2=480.0)
    norm = box.to_normalized(img_w=640, img_h=480)
    assert norm == (0.5, 0.5, 1.0, 1.0)

