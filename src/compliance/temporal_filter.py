from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Deque, Set
from src.common.types import ComplianceStatus

@dataclass
class TemporalComplianceTracker:
    """Maintains a historical voting buffer for a single worker across time."""
    track_id: int
    window_size: int = 15
    violation_history: Deque[Set[str]] = field(default_factory=deque)
    consecutive_violation_count: int = 0
    consecutive_compliant_count: int = 0
    current_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    active_violations: Set[str] = field(default_factory=set)

    def add_frame_observation(self, instant_violations: Set[str]) -> ComplianceStatus:
        """Adds observation from current frame and computes smoothed status."""
        self.violation_history.append(instant_violations)
        if len(self.violation_history) > self.window_size:
            self.violation_history.popleft()

        # Count frequencies of each violation type across window
        violation_counts: Dict[str, int] = {}
        for obs in self.violation_history:
            for v in obs:
                violation_counts[v] = violation_counts.get(v, 0) + 1

        total_frames = len(self.violation_history)
        threshold = 0.50 * total_frames

        persistent_violations = {
            v for v, count in violation_counts.items() if count >= threshold
        }

        if persistent_violations:
            self.consecutive_violation_count += 1
            self.consecutive_compliant_count = 0
            if self.consecutive_violation_count >= 3: # Fast responsive hysteresis (0.1s)
                self.current_status = ComplianceStatus.NON_COMPLIANT
                self.active_violations = persistent_violations
        else:
            self.consecutive_compliant_count += 1
            self.consecutive_violation_count = 0
            if self.consecutive_compliant_count >= 3:
                self.current_status = ComplianceStatus.COMPLIANT
                self.active_violations.clear()

        return self.current_status

