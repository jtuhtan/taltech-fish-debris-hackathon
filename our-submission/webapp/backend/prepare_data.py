#!/usr/bin/env python3
"""Build gallery.json and game.json from REAL model predictions on the test split.

No fabricated data: every entry here comes from predictions.json (our model's
actual output) matched against instances_test.json (the real ground truth).
"""

from __future__ import annotations

import json
from pathlib import Path

DATASET_ROOT = Path("/Users/hinata_shoyo/Desktop/ETH/Data/TalTech-Fish-Debris-Hackathon-v1.0.0")
SUBMISSION = Path("/Users/hinata_shoyo/Desktop/ETH/submission")
OUT_DIR = Path("/Users/hinata_shoyo/Desktop/ETH/webapp/backend/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIDENCE = 0.25
IOU_THRESHOLD = 0.50


def box_iou(a, b) -> float:
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh
    width = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    height = max(0.0, min(ay2, by2) - max(ay1, by1))
    intersection = width * height
    union = aw * ah + bw * bh - intersection
    return intersection / union if union else 0.0


def main() -> None:
    gt = json.loads((DATASET_ROOT / "annotations" / "instances_test.json").read_text())
    preds_raw = json.loads((SUBMISSION / "predictions.json").read_text())

    images = {img["id"]: img for img in gt["images"]}
    gt_boxes_by_image: dict[int, list[list[float]]] = {img_id: [] for img_id in images}
    for ann in gt["annotations"]:
        gt_boxes_by_image[ann["image_id"]].append(ann["bbox"])

    preds_by_image: dict[int, list[dict]] = {img_id: [] for img_id in images}
    for p in preds_raw:
        if p["score"] >= CONFIDENCE:
            preds_by_image[p["image_id"]].append(p)

    gallery = []
    game_false_positives = []
    game_true_negatives = []

    for image_id, image in images.items():
        gt_boxes = gt_boxes_by_image[image_id]
        preds = sorted(preds_by_image[image_id], key=lambda p: -p["score"])

        matched_gt = set()
        matched_preds = []
        unmatched_preds = []
        for p in preds:
            best_idx, best_iou = None, IOU_THRESHOLD
            for i, gb in enumerate(gt_boxes):
                if i in matched_gt:
                    continue
                iou = box_iou(p["bbox"], gb)
                if iou >= best_iou:
                    best_iou = iou
                    best_idx = i
            if best_idx is None:
                unmatched_preds.append(p)
            else:
                matched_gt.add(best_idx)
                matched_preds.append(p)

        is_fish_gt = len(gt_boxes) > 0
        is_fish_pred = len(preds) > 0

        if is_fish_gt and matched_preds:
            status = "true_positive"
        elif is_fish_gt and not matched_preds:
            status = "false_negative"
        elif not is_fish_gt and preds:
            status = "false_positive"
        else:
            status = "true_negative"

        entry = {
            "image_id": image_id,
            "file_name": image["file_name"],
            "width": image["width"],
            "height": image["height"],
            "ground_truth_has_fish": is_fish_gt,
            "ground_truth_boxes": gt_boxes,
            "predicted_has_fish": is_fish_pred,
            "predictions": preds,
            "status": status,
            "condition": image.get("condition", "unknown"),
        }
        gallery.append(entry)

        # real hard-negative false positives for the game (ground truth = no fish, model predicted fish)
        if status == "false_positive":
            game_false_positives.append(entry)
        # real correctly-rejected negatives, for contrast rounds in the game
        if status == "true_negative":
            game_true_negatives.append(entry)

    (OUT_DIR / "gallery.json").write_text(json.dumps(gallery, indent=2))
    (OUT_DIR / "game.json").write_text(
        json.dumps(
            {"false_positives": game_false_positives, "true_negatives": game_true_negatives},
            indent=2,
        )
    )

    status_counts = {}
    for entry in gallery:
        status_counts[entry["status"]] = status_counts.get(entry["status"], 0) + 1

    print("Gallery entries:", len(gallery))
    print("Status breakdown:", status_counts)
    print("Real false-positive frames found for the game:", len(game_false_positives))
    print("True-negative frames available for the game:", len(game_true_negatives))


if __name__ == "__main__":
    main()
