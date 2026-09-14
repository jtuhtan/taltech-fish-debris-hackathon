#!/usr/bin/env python3
"""Score COCO fish predictions using the hackathon benchmark rules."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional manifest.csv used to calculate mean time-band F2",
    )
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.50)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def box_iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + max(0.0, aw), ay1 + max(0.0, ah)
    bx2, by2 = bx1 + max(0.0, bw), by1 + max(0.0, bh)
    width = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    height = max(0.0, min(ay2, by2) - max(ay1, by1))
    intersection = width * height
    union = max(0.0, aw) * max(0.0, ah) + max(0.0, bw) * max(0.0, bh) - intersection
    return intersection / union if union else 0.0


def rates(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    denominator = 4 * precision + recall
    f2 = 5 * precision * recall / denominator if denominator else 0.0
    return {"precision": precision, "recall": recall, "f2": f2}


def time_bands(manifest_path: Path | None) -> dict[str, str]:
    if manifest_path is None:
        return {}
    result: dict[str, str] = {}
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            image_name = Path(row.get("image_file", "")).name
            if image_name:
                result[image_name] = row.get("time_band", "unknown") or "unknown"
    return result


def coco_average_precision(gt_path: Path, predictions: list[dict[str, Any]]) -> tuple[float, float]:
    if not predictions:
        return 0.0, 0.0
    try:
        from pycocotools.coco import COCO
        from pycocotools.cocoeval import COCOeval
    except ImportError as exc:
        raise SystemExit(
            "pycocotools is required for COCO mAP. Run: pip install -r requirements.txt"
        ) from exc

    coco_gt = COCO(str(gt_path))
    coco_dt = coco_gt.loadRes(predictions)
    evaluator = COCOeval(coco_gt, coco_dt, "bbox")
    evaluator.params.catIds = [1]
    evaluator.evaluate()
    evaluator.accumulate()
    evaluator.summarize()
    return max(0.0, float(evaluator.stats[0])), max(0.0, float(evaluator.stats[1]))


def main() -> None:
    args = parse_args()
    ground_truth = load_json(args.ground_truth)
    raw_predictions = load_json(args.predictions)
    if not isinstance(raw_predictions, list):
        raise SystemExit("Predictions must be a JSON list in COCO result format.")

    images = {int(image["id"]): image for image in ground_truth["images"]}
    gt_by_image: dict[int, list[list[float]]] = defaultdict(list)
    for annotation in ground_truth["annotations"]:
        if int(annotation.get("category_id", 1)) == 1:
            gt_by_image[int(annotation["image_id"])].append(annotation["bbox"])

    predictions_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
    valid_predictions: list[dict[str, Any]] = []
    for prediction in raw_predictions:
        image_id = int(prediction["image_id"])
        if image_id not in images:
            raise SystemExit(f"Prediction uses unknown image_id {image_id}.")
        if int(prediction.get("category_id", 1)) != 1:
            continue
        bbox = prediction.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise SystemExit(f"Prediction for image_id {image_id} has an invalid bbox.")
        valid_predictions.append(prediction)
        if float(prediction.get("score", 0.0)) >= args.confidence:
            predictions_by_image[image_id].append(prediction)

    band_by_name = time_bands(args.manifest)
    totals = {"tp": 0, "fp": 0, "fn": 0}
    band_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    negative_frames = negative_frames_with_prediction = 0
    positive_frames = positive_frames_with_match = 0

    for image_id, image in images.items():
        ground_boxes = gt_by_image[image_id]
        predictions = sorted(
            predictions_by_image[image_id],
            key=lambda item: float(item.get("score", 0.0)),
            reverse=True,
        )
        matched: set[int] = set()
        image_tp = 0
        for prediction in predictions:
            best_index = None
            best_iou = args.iou
            for index, ground_box in enumerate(ground_boxes):
                if index in matched:
                    continue
                overlap = box_iou(prediction["bbox"], ground_box)
                if overlap >= best_iou:
                    best_iou = overlap
                    best_index = index
            if best_index is None:
                totals["fp"] += 1
            else:
                matched.add(best_index)
                totals["tp"] += 1
                image_tp += 1

        image_fn = len(ground_boxes) - len(matched)
        totals["fn"] += image_fn
        band = band_by_name.get(Path(image["file_name"]).name, "unknown")
        band_totals[band]["tp"] += image_tp
        band_totals[band]["fp"] += len(predictions) - image_tp
        band_totals[band]["fn"] += image_fn

        if ground_boxes:
            positive_frames += 1
            positive_frames_with_match += int(image_tp > 0)
        else:
            negative_frames += 1
            negative_frames_with_prediction += int(bool(predictions))

    fixed = rates(**totals)
    false_positive_rate = (
        negative_frames_with_prediction / negative_frames if negative_frames else 0.0
    )
    rejection_rate = 1.0 - false_positive_rate
    positive_frame_recall = (
        positive_frames_with_match / positive_frames if positive_frames else 0.0
    )
    band_metrics = {
        band: {**counts, **rates(**counts)}
        for band, counts in sorted(band_totals.items())
        if band != "unknown"
    }
    mean_band_f2 = (
        sum(item["f2"] for item in band_metrics.values()) / len(band_metrics)
        if band_metrics
        else 0.0
    )
    map_50_95, map_50 = coco_average_precision(args.ground_truth, valid_predictions)
    model_points = (
        25 * fixed["f2"]
        + 15 * rejection_rate
        + 10 * map_50_95
        + 10 * mean_band_f2
    )

    result = {
        "operating_point": {"confidence": args.confidence, "iou": args.iou},
        "counts": totals,
        **fixed,
        "positive_frame_recall": positive_frame_recall,
        "no_fish_false_positive_rate": false_positive_rate,
        "no_fish_rejection_rate": rejection_rate,
        "coco_map_50": map_50,
        "coco_map_50_95": map_50_95,
        "time_bands": band_metrics,
        "mean_time_band_f2": mean_band_f2,
        "model_points_out_of_60": model_points,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
