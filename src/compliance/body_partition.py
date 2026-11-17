from dataclasses import dataclass
from typing import Dict
from src.common.types import BoundingBox

@dataclass
class BodyRegions:
    """Anatomical sub-regions within a detected person bounding box."""
    head: BoundingBox
    torso: BoundingBox
    hands: BoundingBox

def partition_worker_body(
    person_box: BoundingBox,
    config: Dict
) -> BodyRegions:
    """
    Partitions a worker's full body bounding box into anatomical sub-regions
    (head, torso, hands) using calibrated vertical and horizontal ratios.
    """
    w = person_box.width
    h = person_box.height
    x1, y1, x2, y2 = person_box.x1, person_box.y1, person_box.x2, person_box.y2
    
    spatial_cfg = config.get("spatial_association", {})
    head_cfg = spatial_cfg.get("head_region", {"top": 0.0, "bottom": 0.30, "horizontal_expansion": 0.15})
    torso_cfg = spatial_cfg.get("torso_region", {"top": 0.20, "bottom": 0.75, "horizontal_expansion": 0.10})
    hands_cfg = spatial_cfg.get("hands_region", {"top": 0.45, "bottom": 0.90, "horizontal_expansion": 0.20})
    
    # 1. Head Region (for Hardhat, NO-Hardhat, Mask, NO-Mask)
    h_exp = head_cfg["horizontal_expansion"] * w
    head_box = BoundingBox(
        x1=x1 - h_exp,
        y1=y1 + head_cfg["top"] * h,
        x2=x2 + h_exp,
        y2=y1 + head_cfg["bottom"] * h
    )
    
    # 2. Torso Region (for Safety Vest, NO-Safety Vest)
    t_exp = torso_cfg["horizontal_expansion"] * w
    torso_box = BoundingBox(
        x1=x1 - t_exp,
        y1=y1 + torso_cfg["top"] * h,
        x2=x2 + t_exp,
        y2=y1 + torso_cfg["bottom"] * h
    )
    
    # 3. Hands / Lower Flanks Region (for Gloves)
    hands_exp = hands_cfg["horizontal_expansion"] * w
    hands_box = BoundingBox(
        x1=x1 - hands_exp,
        y1=y1 + hands_cfg["top"] * h,
        x2=x2 + hands_exp,
        y2=y1 + hands_cfg["bottom"] * h
    )
    
    return BodyRegions(head=head_box, torso=torso_box, hands=hands_box)

