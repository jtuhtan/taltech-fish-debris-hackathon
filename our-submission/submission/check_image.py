#!/usr/bin/env python3
"""Quick manual check: does the model see a fish in this image?

Usage:
    python check_image.py path/to/image.png
    python check_image.py path/to/image.png --weights runs/fish_yolov8n_e20/weights/best.pt
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
DEFAULT_WEIGHTS = HERE / "runs" / "fish_yolov8n_e20" / "weights" / "best.pt"

# the fixed scored operating point used by the official benchmark
CONFIDENCE = 0.25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="path to an image file")
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--imgsz", type=int, default=832)
    parser.add_argument("--device", default="mps")
    parser.add_argument(
        "--save", action="store_true", help="save an annotated copy next to the image"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.image.exists():
        raise FileNotFoundError(args.image)

    model = YOLO(str(args.weights))
    result = model.predict(
        source=str(args.image),
        imgsz=args.imgsz,
        device=args.device,
        conf=CONFIDENCE,
        verbose=False,
    )[0]

    n = len(result.boxes)
    print(f"\nImage: {args.image}")
    if n == 0:
        print("Result: NO FISH")
    else:
        print(f"Result: FISH ({n} detection{'s' if n > 1 else ''})")
        for i, box in enumerate(result.boxes, start=1):
            score = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            print(f"  #{i}: confidence={score:.2f}, box=[{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")

    if args.save:
        out_path = args.image.with_stem(args.image.stem + "_annotated")
        result.save(filename=str(out_path))
        print(f"Annotated image saved to: {out_path}")


if __name__ == "__main__":
    main()
