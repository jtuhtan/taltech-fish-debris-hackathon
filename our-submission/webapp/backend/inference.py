"""Adapter around the real trained fish detector.

Isolated on purpose: the frontend/API never touches Ultralytics directly.
"""

from __future__ import annotations

from pathlib import Path

from ultralytics import YOLO

WEIGHTS_PATH = Path(
    "/Users/hinata_shoyo/Desktop/ETH/submission/runs/fish_yolov8n_e20/weights/best.pt"
)
CONFIDENCE = 0.25  # the fixed scored operating point used by the hackathon benchmark
IMGSZ = 832

_model: YOLO | None = None


def load_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO(str(WEIGHTS_PATH))
    return _model


def predict(image_path: str, device: str = "mps") -> list[dict]:
    """Run the real model on an image. Returns a list of {bbox, confidence}."""
    model = load_model()
    result = model.predict(
        source=image_path, imgsz=IMGSZ, device=device, conf=CONFIDENCE, verbose=False
    )[0]

    detections = []
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append(
            {
                "bbox": [x1, y1, x2 - x1, y2 - y1],
                "confidence": float(box.conf[0]),
            }
        )
    return detections


def annotate_image(image_path: str, out_path: str, device: str = "mps") -> list[dict]:
    """Run the model and save an annotated copy with real boxes drawn. Returns detections."""
    model = load_model()
    result = model.predict(
        source=image_path, imgsz=IMGSZ, device=device, conf=CONFIDENCE, verbose=False
    )[0]
    result.save(filename=out_path)

    detections = []
    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append(
            {
                "bbox": [x1, y1, x2 - x1, y2 - y1],
                "confidence": float(box.conf[0]),
            }
        )
    return detections
