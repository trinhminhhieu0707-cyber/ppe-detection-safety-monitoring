import os
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
import yaml

from src.common.types import ComplianceStatus, Detection, BoundingBox
from src.tracking.tracker import TrackedPerson
from src.compliance.association import SpatialAssociator
from src.compliance.temporal_filter import TemporalComplianceTracker

@dataclass
class ViolationEvent:
    """Represents a validated safety violation event ready for database logging."""
    event_id: str
    track_id: int
    timestamp: float
    violations: List[str]
    worker_box: BoundingBox
    status: str = "OPEN" # OPEN, ACKNOWLEDGED, RESOLVED

@dataclass
class WorkerComplianceState:
    """Full real-time state for an individual tracked worker."""
    track_id: int
    box: BoundingBox
    status: ComplianceStatus
    active_violations: List[str]
    detected_ppe: List[str]
    confidence: float


class PPEComplianceEngine:
    """Production PPE Safety Compliance Engine with Spatial Association & Temporal Voting."""

    def __init__(self, config_path: str = "configs/compliance_rules.yaml"):
        self.config_path = config_path
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.rules = self.config.get("rules", {})
        self.associator = SpatialAssociator(self.config)
        self.worker_trackers: Dict[int, TemporalComplianceTracker] = {}
        self.logged_events: Dict[int, ViolationEvent] = {} # Active open events per track_id

    def process_frame(
        self,
        workers: List[TrackedPerson],
        ppe_detections: List[Detection]
    ) -> Tuple[List[WorkerComplianceState], List[ViolationEvent]]:
        """
        Main processing method called per frame:
        1. Associates PPE items with worker body partitions.
        2. Evaluates compliance rules per worker.
        3. Applies temporal voting to eliminate flicker.
        4. Emits active violation events.
        """
        states: List[WorkerComplianceState] = []
        new_events: List[ViolationEvent] = []

        if not workers:
            return states, new_events

        # 1. Spatial Association
        associations = self.associator.associate(workers, ppe_detections)

        current_frame_worker_ids = set()

        for worker in workers:
            tid = worker.track_id
            current_frame_worker_ids.add(tid)
            w_items = associations.get(tid, {})

            # 2. Instantaneous Rule Checking
            instant_violations: Set[str] = set()
            detected_ppe: List[str] = []

            # Check Hardhat
            if self.rules.get("require_hardhat", True):
                has_hat = any(d.class_name == 'Hardhat' for d in w_items.get('hardhat', []))
                has_no_hat = any(d.class_name == 'NO-Hardhat' for d in w_items.get('hardhat', []))
                if has_hat:
                    detected_ppe.append("Hardhat")
                if has_no_hat:
                    instant_violations.add("NO-Hardhat")

            # Check Safety Vest
            if self.rules.get("require_safety_vest", True):
                has_vest = any(d.class_name == 'Safety Vest' for d in w_items.get('safety_vest', []))
                has_no_vest = any(d.class_name == 'NO-Safety Vest' for d in w_items.get('safety_vest', []))
                if has_vest:
                    detected_ppe.append("Safety Vest")
                if has_no_vest:
                    instant_violations.add("NO-Safety Vest")

            # Check Mask
            if self.rules.get("require_mask", False):
                has_mask = any(d.class_name == 'Mask' for d in w_items.get('mask', []))
                has_no_mask = any(d.class_name == 'NO-Mask' for d in w_items.get('mask', []))
                if has_mask:
                    detected_ppe.append("Mask")
                if has_no_mask:
                    instant_violations.add("NO-Mask")

            # Check Gloves
            if self.rules.get("require_gloves", False):
                has_gloves = any(d.class_name == 'Gloves' for d in w_items.get('gloves', []))
                if has_gloves:
                    detected_ppe.append("Gloves")

            # 3. Temporal Voting
            if tid not in self.worker_trackers:
                self.worker_trackers[tid] = TemporalComplianceTracker(
                    track_id=tid,
                    window_size=self.config.get("temporal_filtering", {}).get("history_window_size", 15)
                )

            status = self.worker_trackers[tid].add_frame_observation(instant_violations)
            active_viols = list(self.worker_trackers[tid].active_violations)

            # 4. Event Detection & Lifecycle
            if status == ComplianceStatus.NON_COMPLIANT and active_viols:
                if tid not in self.logged_events:
                    event = ViolationEvent(
                        event_id=str(uuid.uuid4())[:8],
                        track_id=tid,
                        timestamp=time.time(),
                        violations=active_viols,
                        worker_box=worker.box,
                        status="OPEN"
                    )
                    self.logged_events[tid] = event
                    new_events.append(event)
            elif status == ComplianceStatus.COMPLIANT:
                if tid in self.logged_events:
                    # Violation resolved
                    del self.logged_events[tid]

            states.append(WorkerComplianceState(
                track_id=tid,
                box=worker.box,
                status=status,
                active_violations=active_viols,
                detected_ppe=detected_ppe,
                confidence=worker.confidence
            ))

        # Cleanup memory for departed workers
        stale_workers = [w_id for w_id in self.worker_trackers if w_id not in current_frame_worker_ids]
        for w_id in stale_workers:
            # If departed, clear event
            if w_id in self.logged_events:
                del self.logged_events[w_id]
            del self.worker_trackers[w_id]

        return states, new_events

