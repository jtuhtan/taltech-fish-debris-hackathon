#!/usr/bin/env python3
"""Run the frozen fish detector on the test split and export COCO predictions.

Exports every detection down to a very low confidence so the official
evaluator (which applies its own conf=0.25 threshold for F2/rejection, but
uses the full score range for COCO mAP50:95) has what it needs.

Usage:
    python predict_test.py --weights runs/fish_yolov8n_e20/weights/best.pt \
        --output predictions.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
DATASET_ROOT = Path("/Users/hinata_shoyo/Desktop/ETH/Data/TalTech-Fish-Debris-Hackathon-v1.0.0")
INSTANCES_TEST = DATASET_ROOT / "annotations" / "instances_test.json"
IMAGES_TEST = DATASET_ROOT / "images" / "test"

FISH_CATEGORY_ID = 1  # from instances_test.json "categories"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--output", default=HERE / "predictions.json", type=Path)
    parser.add_argument("--imgsz", type=int, default=832)
    parser.add_argument("--device", default="mps")
    parser.add_argument(
        "--conf",
        type=float,
        default=0.001,
        help="export threshold (low, not the scored operating point of 0.25)",
    )
    return parser.parse_args()


def load_file_name_to_id() -> dict[str, int]:
    with INSTANCES_TEST.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {image["file_name"]: image["id"] for image in data["images"]}


def main() -> None:
    args = parse_args()
    file_name_to_id = load_file_name_to_id()

    model = YOLO(str(args.weights))
    predictions: list[dict] = []

    for file_name, image_id in file_name_to_id.items():
        image_path = IMAGES_TEST / file_name
        if not image_path.exists():
            raise FileNotFoundError(image_path)

        result = model.predict(
            source=str(image_path),
            imgsz=args.imgsz,
            device=args.device,
            conf=args.conf,
            verbose=False,
        )[0]

        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            score = float(box.conf[0])
            predictions.append(
                {
                    "image_id": image_id,
                    "category_id": FISH_CATEGORY_ID,
                    "bbox": [x1, y1, x2 - x1, y2 - y1],
                    "score": score,
                }
            )

    args.output.write_text(json.dumps(predictions, indent=2), encoding="utf-8")
    print(f"Wrote {len(predictions)} predictions across {len(file_name_to_id)} images to {args.output}")


if __name__ == "__main__":
    main()
