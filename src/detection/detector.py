import os
import time
from typing import List, Dict, Union, Optional
import numpy as np
import yaml

from src.common.types import Detection, BoundingBox

class PPEDetector:
    """Production Object Detector supporting both PyTorch (.pt) and ONNX (.onnx) formats."""

    def __init__(
        self,
        model_path: str,
        config_path: Optional[str] = "configs/data_ppe.yaml",
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.50,
        device: str = "auto"
    ):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        
        # Load class names from config if available
        self.class_names: Dict[int, str] = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                names = cfg.get("names", {})
                if isinstance(names, list):
                    self.class_names = {i: name for i, name in enumerate(names)}
                elif isinstance(names, dict):
                    self.class_names = {int(k): v for k, v in names.items()}

        self.is_onnx = model_path.endswith(".onnx")
        self._init_model()

    def _init_model(self) -> None:
        if self.is_onnx:
            self._init_onnx()
        else:
            self._init_yolo()

    def _init_yolo(self) -> None:
        from ultralytics import YOLO
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model weights not found at: {self.model_path}")
        self.model = YOLO(self.model_path)
        # Fallback to model names if config was empty
        if not self.class_names and hasattr(self.model, "names"):
            self.class_names = self.model.names

    def _init_onnx(self) -> None:
        from ultralytics import YOLO
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"ONNX model file not found at: {self.model_path}")
        self.onnx_yolo = YOLO(self.model_path, task='detect')
        if not self.class_names and hasattr(self.onnx_yolo, "names"):
            self.class_names = self.onnx_yolo.names

    def predict(self, image: np.ndarray) -> List[Detection]:
        """Perform inference on a single BGR OpenCV image and return parsed detections."""
        if self.is_onnx:
            return self._predict_onnx(image)
        return self._predict_yolo(image)

    def _predict_yolo(self, image: np.ndarray) -> List[Detection]:
        results = self.model.predict(
            source=image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            device=self.device if self.device != "auto" else None,
            verbose=False
        )
        
        detections: List[Detection] = []
        if not results:
            return detections
            
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return detections
            
        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls_id = int(boxes.cls[i].cpu().numpy())
            cls_name = self.class_names.get(cls_id, f"Class_{cls_id}")
            
            box = BoundingBox(
                x1=float(xyxy[0]),
                y1=float(xyxy[1]),
                x2=float(xyxy[2]),
                y2=float(xyxy[3])
            )
            detections.append(Detection(
                box=box,
                confidence=conf,
                class_id=cls_id,
                class_name=cls_name
            ))
            
        return detections

    def _predict_onnx(self, image: np.ndarray) -> List[Detection]:
        """ONNX Runtime inference (Optimized single-session pipeline)."""
        results = self.onnx_yolo.predict(source=image, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)
        detections = []
        if results and len(results[0].boxes) > 0:
            for b in results[0].boxes:
                xy = b.xyxy[0].cpu().numpy()
                cls_id = int(b.cls[0].cpu().numpy())
                detections.append(Detection(
                    box=BoundingBox(float(xy[0]), float(xy[1]), float(xy[2]), float(xy[3])),
                    confidence=float(b.conf[0].cpu().numpy()),
                    class_id=cls_id,
                    class_name=self.class_names.get(cls_id, f"Class_{cls_id}")
                ))
        return detections

    def benchmark(self, image: np.ndarray, num_runs: int = 30) -> Dict[str, float]:
        """Measure latency (ms) and throughput (FPS) across multiple iterations."""
        # Warm-up runs
        for _ in range(5):
            self.predict(image)
            
        times = []
        for _ in range(num_runs):
            t0 = time.perf_counter()
            self.predict(image)
            times.append((time.perf_counter() - t0) * 1000.0) # in ms
            
        mean_ms = float(np.mean(times))
        std_ms = float(np.std(times))
        fps = 1000.0 / mean_ms if mean_ms > 0 else 0.0
        
        return {
            "mean_latency_ms": round(mean_ms, 2),
            "std_latency_ms": round(std_ms, 2),
            "fps": round(fps, 1),
            "num_runs": num_runs
        }

