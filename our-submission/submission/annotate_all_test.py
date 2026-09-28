#!/usr/bin/env python3
"""Save an annotated (boxed) copy of every test-split image for the demo/pitch.

Usage:
    python annotate_all_test.py --weights runs/fish_yolov8n_e20/weights/best.pt
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
DATASET_ROOT = Path("/Users/hinata_shoyo/Desktop/ETH/Data/TalTech-Fish-Debris-Hackathon-v1.0.0")
IMAGES_TEST = DATASET_ROOT / "images" / "test"

# the fixed scored operating point used by the official benchmark
CONFIDENCE = 0.25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=HERE / "annotated_test")
    parser.add_argument("--imgsz", type=int, default=832)
    parser.add_argument("--device", default="mps")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(args.weights))
    images = sorted(IMAGES_TEST.glob("*.png"))

    fish_count = 0
    no_fish_count = 0
    for i, image_path in enumerate(images, start=1):
        result = model.predict(
            source=str(image_path),
            imgsz=args.imgsz,
            device=args.device,
            conf=CONFIDENCE,
            verbose=False,
        )[0]

        n = len(result.boxes)
        tag = "FISH" if n else "NOFISH"
        if n:
            fish_count += 1
        else:
            no_fish_count += 1

        out_path = args.output_dir / f"{tag}_{image_path.stem}.png"
        result.save(filename=str(out_path))

        if i % 20 == 0 or i == len(images):
            print(f"{i}/{len(images)} done")

    print(f"\nSaved {len(images)} annotated images to {args.output_dir}")
    print(f"Predicted FISH: {fish_count}, predicted NO FISH: {no_fish_count}")


if __name__ == "__main__":
    main()
