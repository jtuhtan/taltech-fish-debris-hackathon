#!/usr/bin/env python3
"""Validate a built hackathon dataset and fail on integrity problems."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    root = args.dataset
    with (root / "metadata" / "manifest.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1200, f"expected 1200 images, found {len(rows)}"
    assert len({row["frame_id"] for row in rows}) == len(rows), "duplicate frame IDs"
    assert sum(int(row["annotation_count"]) for row in rows) >= 1000

    group_splits = defaultdict(set)
    split_counts = Counter()
    status_counts = Counter()
    box_counts = Counter()
    for row in rows:
        split = row["split"]
        fid = row["frame_id"]
        path = root / row["image_file"]
        label = root / "labels" / "yolo" / split / f"{fid}.txt"
        assert path.is_file(), f"missing image: {path}"
        assert label.is_file(), f"missing label: {label}"
        assert "f-" + sha256(path)[:12] == fid, f"content hash mismatch: {path}"
        lines = [line for line in label.read_text(encoding="utf-8").splitlines() if line]
        assert len(lines) == int(row["annotation_count"]), f"label count mismatch: {fid}"
        for line in lines:
            fields = line.split()
            assert len(fields) == 5 and fields[0] == "0", f"bad YOLO row: {fid}"
            values = list(map(float, fields[1:]))
            assert all(0.0 <= value <= 1.0 for value in values), f"YOLO bounds: {fid}"
            assert values[2] > 0 and values[3] > 0, f"degenerate YOLO box: {fid}"
        group_splits[row["capture_group"]].add(split)
        split_counts[split] += 1
        status_counts[(split, row["status"])] += 1
        box_counts[split] += len(lines)
    leaking = [group for group, splits in group_splits.items() if len(splits) > 1]
    assert not leaking, f"capture groups cross splits: {leaking[:5]}"
    assert split_counts == Counter({"train": 840, "validation": 180, "test": 180})
    for split in ("train", "validation", "test"):
        assert status_counts[(split, "fish")] > 0
        assert status_counts[(split, "no_fish")] > 0
        coco = json.loads((root / "annotations" / f"instances_{split}.json").read_text())
        assert len(coco["images"]) == split_counts[split]
        assert len(coco["annotations"]) == box_counts[split]
    print(json.dumps({
        "status": "valid",
        "images": len(rows),
        "fish_boxes": sum(box_counts.values()),
        "split_images": dict(split_counts),
        "split_boxes": dict(box_counts),
        "capture_groups": len(group_splits),
        "cross_split_capture_groups": len(leaking),
    }, indent=2))


if __name__ == "__main__":
    main()
