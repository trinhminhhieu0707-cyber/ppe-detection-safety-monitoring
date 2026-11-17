from dataclasses import dataclass
from typing import Tuple, List, Optional
from enum import Enum

class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    UNKNOWN = "UNKNOWN"

@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def to_xyxy(self) -> Tuple[int, int, int, int]:
        return (int(self.x1), int(self.y1), int(self.x2), int(self.y2))

    def to_normalized(self, img_w: int, img_h: int) -> Tuple[float, float, float, float]:
        return (self.x1 / img_w, self.y1 / img_h, self.x2 / img_w, self.y2 / img_h)

@dataclass
class Detection:
    box: BoundingBox
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None

# BGR Color Palette for CV2 Visualization
# Green: Compliance, Red: Violation, Blue: Person, Orange: Cone
CLASS_COLORS = {
    'Person': (220, 120, 40),          # Soft Blue
    'Hardhat': (46, 204, 113),         # Bright Emerald Green
    'NO-Hardhat': (41, 41, 231),       # Vibrant Red
    'Safety Vest': (46, 204, 113),     # Bright Emerald Green
    'NO-Safety Vest': (41, 41, 231),   # Vibrant Red
    'Mask': (46, 204, 113),            # Bright Emerald Green
    'NO-Mask': (41, 41, 231),          # Vibrant Red
    'Gloves': (46, 204, 113),          # Bright Emerald Green
    'Safety Cone': (0, 140, 255)       # Safety Orange
}

DEFAULT_COLOR = (200, 200, 200)

PPE_CLASSES = {'Hardhat', 'Safety Vest', 'Mask', 'Gloves'}
VIOLATION_CLASSES = {'NO-Hardhat', 'NO-Safety Vest', 'NO-Mask'}

