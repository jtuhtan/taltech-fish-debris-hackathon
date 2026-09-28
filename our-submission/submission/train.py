#!/usr/bin/env python3
"""Fine-tune a YOLO detector for the TalTech fish-vs-debris hackathon.

Usage:
    python train.py --epochs 100 --imgsz 832 --model yolov8n.pt --device mps
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
DATA_YAML = HERE / "data.yaml"
SEED = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="yolov8n.pt", help="pretrained weights to start from")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=832)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--patience", type=int, default=20, help="early-stop patience (epochs)")
    parser.add_argument("--device", default="mps", help="mps, cpu, or a CUDA device index")
    parser.add_argument("--name", default="fish_yolov8n", help="run name under submission/runs/")
    return parser.parse_args()


def resolve_device(requested: str) -> str:
    if requested == "mps" and not torch.backends.mps.is_available():
        print("MPS not available on this machine, falling back to CPU.")
        return "cpu"
    return requested


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)

    if not DATA_YAML.exists():
        raise FileNotFoundError(f"data.yaml not found at {DATA_YAML}")

    model = YOLO(args.model)
    model.train(
        data=str(DATA_YAML),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device=device,
        seed=SEED,
        project=str(HERE / "runs"),
        name=args.name,
        exist_ok=True,
        # dataset is small and single-class; keep augmentation mild so we don't
        # distort the fish shapes/scale the challenge is actually testing.
        degrees=0.0,
        shear=0.0,
        perspective=0.0,
    )
    print(f"\nDone. Best weights: {HERE / 'runs' / args.name / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
