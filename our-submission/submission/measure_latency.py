#!/usr/bin/env python3
"""Measure inference latency (p50/p95) and model size for edge-readiness reporting."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from ultralytics import YOLO

DATASET_ROOT = Path("/Users/hinata_shoyo/Desktop/ETH/Data/TalTech-Fish-Debris-Hackathon-v1.0.0")
IMAGES_TEST = DATASET_ROOT / "images" / "test"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--imgsz", type=int, default=832)
    parser.add_argument("--device", default="mps")
    parser.add_argument("--n", type=int, default=100, help="number of images to time")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(str(args.weights))
    images = sorted(IMAGES_TEST.glob("*.png"))[: args.n]

    # warmup
    for image in images[:5]:
        model.predict(source=str(image), imgsz=args.imgsz, device=args.device, verbose=False)

    times_ms = []
    for image in images:
        start = time.perf_counter()
        model.predict(source=str(image), imgsz=args.imgsz, device=args.device, verbose=False)
        times_ms.append((time.perf_counter() - start) * 1000)

    times_ms.sort()
    p50 = times_ms[len(times_ms) // 2]
    p95 = times_ms[int(len(times_ms) * 0.95)]
    size_mb = args.weights.stat().st_size / (1024 * 1024)

    print(f"Images timed: {len(times_ms)}")
    print(f"p50 latency: {p50:.2f} ms")
    print(f"p95 latency: {p95:.2f} ms")
    print(f"mean latency: {sum(times_ms) / len(times_ms):.2f} ms")
    print(f"FPS (batch=1, p50): {1000 / p50:.1f}")
    print(f"Model size: {size_mb:.2f} MB")
    print(f"Device: {args.device}, imgsz: {args.imgsz}, batch: 1, precision: fp32")


if __name__ == "__main__":
    main()
