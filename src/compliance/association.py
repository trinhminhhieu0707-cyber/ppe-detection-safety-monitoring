from typing import List, Dict, Tuple, Optional
from src.common.types import Detection, BoundingBox
from src.tracking.tracker import TrackedPerson
from src.compliance.body_partition import partition_worker_body, BodyRegions

def compute_intersection_area(b1: BoundingBox, b2: BoundingBox) -> float:
    """Computes intersection area between two bounding boxes."""
    ix1 = max(b1.x1, b2.x1)
    iy1 = max(b1.y1, b2.y1)
    ix2 = min(b1.x2, b2.x2)
    iy2 = min(b1.y2, b2.y2)
    
    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    return inter_w * inter_h

def compute_containment_ratio(item_box: BoundingBox, region_box: BoundingBox) -> float:
    """Computes the ratio of item area contained inside the body region."""
    item_area = item_box.area
    if item_area <= 0:
        return 0.0
    inter_area = compute_intersection_area(item_box, region_box)
    return inter_area / item_area

class SpatialAssociator:
    """Associates PPE items with workers based on anatomical body region geometry."""

    def __init__(self, config: Dict):
        self.config = config
        spatial_cfg = config.get("spatial_association", {})
        self.min_overlap_ratio = spatial_cfg.get("min_overlap_ratio", 0.40)

    def associate(
        self,
        workers: List[TrackedPerson],
        ppe_detections: List[Detection]
    ) -> Dict[int, Dict[str, List[Detection]]]:
        """
        Maps worker track_id -> dict of associated items:
        {
            track_id: {
                'hardhat': [...],
                'safety_vest': [...],
                'mask': [...],
                'gloves': [...]
            }
        }
        """
        associations: Dict[int, Dict[str, List[Detection]]] = {
            w.track_id: {
                'hardhat': [],
                'safety_vest': [],
                'mask': [],
                'gloves': []
            }
            for w in workers
        }

        # Precompute body partitions for each worker
        worker_regions: Dict[int, BodyRegions] = {
            w.track_id: partition_worker_body(w.box, self.config)
            for w in workers
        }

        for item in ppe_detections:
            cls_name = item.class_name
            best_worker_id: Optional[int] = None
            highest_overlap: float = 0.0

            # Determine target anatomical region
            if cls_name in ('Hardhat', 'NO-Hardhat'):
                category = 'hardhat'
                for w in workers:
                    overlap = compute_containment_ratio(item.box, worker_regions[w.track_id].head)
                    if overlap > highest_overlap and overlap >= self.min_overlap_ratio:
                        highest_overlap = overlap
                        best_worker_id = w.track_id

            elif cls_name in ('Safety Vest', 'NO-Safety Vest'):
                category = 'safety_vest'
                for w in workers:
                    overlap = compute_containment_ratio(item.box, worker_regions[w.track_id].torso)
                    if overlap > highest_overlap and overlap >= self.min_overlap_ratio:
                        highest_overlap = overlap
                        best_worker_id = w.track_id

            elif cls_name in ('Mask', 'NO-Mask'):
                category = 'mask'
                for w in workers:
                    overlap = compute_containment_ratio(item.box, worker_regions[w.track_id].head)
                    if overlap > highest_overlap and overlap >= self.min_overlap_ratio:
                        highest_overlap = overlap
                        best_worker_id = w.track_id

            elif cls_name == 'Gloves':
                category = 'gloves'
                for w in workers:
                    overlap = compute_containment_ratio(item.box, worker_regions[w.track_id].hands)
                    if overlap > highest_overlap and overlap >= self.min_overlap_ratio:
                        highest_overlap = overlap
                        best_worker_id = w.track_id
            else:
                continue

            if best_worker_id is not None:
                associations[best_worker_id][category].append(item)

        return associations

