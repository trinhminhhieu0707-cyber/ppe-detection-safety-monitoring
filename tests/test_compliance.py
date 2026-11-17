import pytest
from src.common.types import BoundingBox, ComplianceStatus
from src.compliance.body_partition import partition_worker_body
from src.compliance.association import compute_containment_ratio
from src.compliance.temporal_filter import TemporalComplianceTracker

def test_body_partitioning():
    person = BoundingBox(x1=100.0, y1=100.0, x2=200.0, y2=400.0) # H=300, W=100
    cfg = {
        "spatial_association": {
            "head_region": {"top": 0.0, "bottom": 0.30, "horizontal_expansion": 0.1},
            "torso_region": {"top": 0.25, "bottom": 0.75, "horizontal_expansion": 0.1},
            "hands_region": {"top": 0.50, "bottom": 0.90, "horizontal_expansion": 0.2}
        }
    }
    regions = partition_worker_body(person, cfg)
    
    # Head should span y1=100 to y2=190 (30% of 300)
    assert regions.head.y1 == 100.0
    assert regions.head.y2 == 190.0
    # Torso should span y1=175 to y2=325
    assert regions.torso.y1 == 175.0
    assert regions.torso.y2 == 325.0

def test_containment_ratio():
    region = BoundingBox(x1=50.0, y1=50.0, x2=150.0, y2=150.0)
    # Fully inside
    item_inside = BoundingBox(x1=60.0, y1=60.0, x2=80.0, y2=80.0)
    assert compute_containment_ratio(item_inside, region) == 1.0
    
    # Completely outside
    item_outside = BoundingBox(x1=200.0, y1=200.0, x2=250.0, y2=250.0)
    assert compute_containment_ratio(item_outside, region) == 0.0

def test_temporal_voting_filter():
    tracker = TemporalComplianceTracker(track_id=1, window_size=10)
    
    # Feed compliant observations
    for _ in range(6):
        status = tracker.add_frame_observation(set())
    assert status == ComplianceStatus.COMPLIANT
    
    # Feed transient violation (only 2 frames) -> should not trigger non-compliant
    tracker.add_frame_observation({"NO-Hardhat"})
    tracker.add_frame_observation({"NO-Hardhat"})
    assert tracker.current_status == ComplianceStatus.COMPLIANT
    
    # Feed sustained violations (6 frames) -> should trigger non-compliant
    for _ in range(6):
        status = tracker.add_frame_observation({"NO-Hardhat"})
    assert status == ComplianceStatus.NON_COMPLIANT

