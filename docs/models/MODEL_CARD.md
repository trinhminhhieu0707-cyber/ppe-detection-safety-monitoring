# MODEL CARD: PPE-YOLO11s-SAFETY-MONITOR

## Model Details
- **Architecture:** YOLO11s (Ultralytics)
- **Task:** Object Detection for Construction Site Personal Protective Equipment
- **Framework:** PyTorch 2.14 / ONNX Runtime
- **Input Format:** RGB/BGR Images, $640 \times 640 \times 3$
- **Output:** Bounding boxes $(x_1, y_1, x_2, y_2)$, confidence scores, class IDs ($0 \dots 8$)
- **Parameters:** 9,416,283 (~9.4M)
- **Computational Complexity:** 21.4 GFLOPs
- **Inference Latency:** 9.6 ms (Tesla T4 GPU), ~35 ms (Intel 12th Gen CPU via ONNX Runtime)

## Intended Use
- **Primary Use Case:** Real-time PPE compliance tracking on CCTV / RTSP video streams at construction sites.
- **Target Objects:** Construction workers (`Person`), hard hats (`Hardhat`, `NO-Hardhat`), safety vests (`Safety Vest`, `NO-Safety Vest`), masks (`Mask`, `NO-Mask`), gloves (`Gloves`), safety cones (`Safety Cone`).
- **Out-of-Scope:** Facial recognition, identity verification, biometrics.

## Performance Metrics (Test Set)
- **Mean Latency:** 9.6 ms per frame (104.2 FPS)
- **Precision (All):** 82.1%
- **Recall (All):** 58.0%
- **mAP@50:** 63.4%
- **mAP@50-95:** 38.0%

## Limitations & Mitigations
- **Small Object Distance:** At distances $> 25\text{m}$, gloves and masks may experience lower recall. 
- **Mitigation:** Addressed in Phase 04 via Temporal Voting and Worker-Centric Spatial Association.

