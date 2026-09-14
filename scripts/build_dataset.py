#!/usr/bin/env python3
"""Build the TalTech fish-vs-drift hackathon dataset from Fishbox projects.

The builder is deterministic. It resolves Fishbox content-hash frame IDs,
profiles simple visual conditions, samples broadly across deployment/date/time/
condition strata, and assigns 10-minute capture groups wholly to one split.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
SPLIT_TARGETS = {"train": 0.70, "validation": 0.15, "test": 0.15}


@dataclass
class Candidate:
    frame_id: str
    path: Path
    project: str
    source: str
    status: str
    boxes: list[dict]
    captured_at: str
    date: str
    hour: int
    time_band: str
    brightness: float
    contrast: float
    edge_energy: float
    brightness_band: str
    contrast_band: str
    texture_band: str
    color_cast: str
    width: int
    height: int
    split: str = ""

    @property
    def annotation_count(self) -> int:
        return len(self.boxes)

    @property
    def condition(self) -> str:
        return "/".join(
            (self.brightness_band, self.contrast_band, self.texture_band, self.color_cast)
        )

    @property
    def group(self) -> str:
        minute = 0
        if self.captured_at:
            minute = int(self.captured_at[14:16]) // 10
        return f"{self.source}|{self.date}|{self.hour:02d}|{minute}"


def frame_id(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "f-" + digest.hexdigest()[:12]


def source_name(path: Path) -> str:
    text = path.as_posix()
    match = re.search(r"/(IAHC2407|PIKE)/", text, flags=re.I)
    if match:
        return match.group(1).upper()
    match = re.search(r"annotation frames/(\d{8})", text, flags=re.I)
    if match:
        return "EDGE_DEVICE"
    return path.parent.name.upper() or "UNKNOWN"


def capture_time(path: Path) -> tuple[str, str, int, str]:
    text = path.as_posix()
    dates = re.findall(r"(?<!\d)(20\d{6})(?!\d)", text)
    date_token = dates[-1] if dates else ""
    time_match = re.match(r"(\d{2})(\d{2})(\d{2})", path.stem)
    if not date_token or not time_match:
        return "", date_token, -1, "unknown"
    hour, minute, second = map(int, time_match.groups())
    try:
        stamp = datetime.strptime(
            f"{date_token}{hour:02d}{minute:02d}{second:02d}", "%Y%m%d%H%M%S"
        )
    except ValueError:
        return "", date_token, -1, "unknown"
    if 6 <= hour <= 8:
        band = "dawn"
    elif 9 <= hour <= 17:
        band = "day"
    elif 18 <= hour <= 20:
        band = "dusk"
    else:
        band = "night"
    return stamp.isoformat(), stamp.date().isoformat(), hour, band


def visual_profile(path: Path) -> tuple:
    with Image.open(path) as image:
        width, height = image.size
        rgb = image.convert("RGB")
        rgb.thumbnail((160, 160))
        gray = rgb.convert("L")
        stat = ImageStat.Stat(gray)
        brightness = float(stat.mean[0])
        contrast = float(stat.stddev[0])
        edge_energy = float(ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0])
        means = ImageStat.Stat(rgb).mean
    brightness_band = "dark" if brightness < 70 else "bright" if brightness > 160 else "mid"
    contrast_band = "low" if contrast < 25 else "high" if contrast > 55 else "medium"
    texture_band = "smooth" if edge_energy < 12 else "textured" if edge_energy > 30 else "medium"
    r, g, b = means
    if r > g * 1.08 and r > b * 1.08:
        color_cast = "warm-brown"
    elif b > r * 1.08 and b > g * 1.04:
        color_cast = "blue"
    elif g > r * 1.06 and g > b * 1.03:
        color_cast = "green"
    else:
        color_cast = "neutral"
    return (
        brightness,
        contrast,
        edge_energy,
        brightness_band,
        contrast_band,
        texture_band,
        color_cast,
        width,
        height,
    )


def discover_projects(root: Path) -> list[tuple[str, dict, dict]]:
    projects = []
    for project_dir in sorted((root / "projects").iterdir()):
        manifest_path = project_dir / "project.json"
        annotations_path = project_dir / "annotations.json"
        if not manifest_path.exists() or not annotations_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        store = json.loads(annotations_path.read_text(encoding="utf-8"))
        if store.get("annotations") or store.get("no_fish"):
            projects.append((project_dir.name, manifest, store))
    return projects


def build_index(projects: list[tuple[str, dict, dict]]) -> tuple[dict[str, Path], dict[str, str]]:
    paths: dict[str, Path] = {}
    sources: dict[str, str] = {}
    unique_dirs = []
    seen_dirs = set()
    for _, manifest, store in projects:
        for raw in list(manifest.get("sources", [])) + list(store.get("sources", [])):
            directory = Path(raw)
            key = str(directory)
            if key not in seen_dirs and directory.is_dir():
                seen_dirs.add(key)
                unique_dirs.append(directory)
    for number, directory in enumerate(unique_dirs, 1):
        files = sorted(
            p for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )
        print(f"Indexing {number}/{len(unique_dirs)}: {directory} ({len(files)} files)", flush=True)
        src = source_name(directory / "placeholder")
        for path in files:
            fid = frame_id(path)
            paths.setdefault(fid, path)
            sources.setdefault(fid, src)
    return paths, sources


def load_candidates(root: Path) -> tuple[list[Candidate], dict]:
    projects = discover_projects(root)
    index, source_by_id = build_index(projects)
    records: dict[str, dict] = {}
    overlaps = 0
    for project, _, store in projects:
        for fid, raw_boxes in store.get("annotations", {}).items():
            boxes = raw_boxes if isinstance(raw_boxes, list) else [raw_boxes]
            if fid in records:
                overlaps += 1
                continue
            records[fid] = {"project": project, "status": "fish", "boxes": boxes}
        for fid in store.get("no_fish", []):
            records.setdefault(fid, {"project": project, "status": "no_fish", "boxes": []})

    missing = sorted(set(records) - set(index))
    candidates = []
    for number, (fid, record) in enumerate(sorted(records.items()), 1):
        path = index.get(fid)
        if path is None:
            continue
        try:
            profile = visual_profile(path)
        except Exception as exc:
            print(f"Skipping undecodable {path}: {exc}", file=sys.stderr)
            continue
        captured_at, date, hour, time_band = capture_time(path)
        candidates.append(
            Candidate(
                frame_id=fid,
                path=path,
                project=record["project"],
                source=source_by_id.get(fid, source_name(path)),
                status=record["status"],
                boxes=record["boxes"],
                captured_at=captured_at,
                date=date or "unknown",
                hour=hour,
                time_band=time_band,
                brightness=profile[0],
                contrast=profile[1],
                edge_energy=profile[2],
                brightness_band=profile[3],
                contrast_band=profile[4],
                texture_band=profile[5],
                color_cast=profile[6],
                width=profile[7],
                height=profile[8],
            )
        )
        if number % 500 == 0:
            print(f"Profiled {number}/{len(records)} records", flush=True)
    audit = {
        "projects": [p[0] for p in projects],
        "records_total": len(records),
        "resolved_records": len(candidates),
        "missing_records": len(missing),
        "missing_frame_ids": missing,
        "duplicate_project_records_ignored": overlaps,
    }
    return candidates, audit


def stable_rank(candidate: Candidate, seed: str) -> str:
    return hashlib.sha256(f"{seed}:{candidate.frame_id}".encode()).hexdigest()


def diverse_sample(pool: list[Candidate], target_frames: int, seed: str) -> list[Candidate]:
    strata: dict[tuple, list[Candidate]] = defaultdict(list)
    for item in pool:
        key = (item.project, item.source, item.date, item.time_band, item.condition)
        strata[key].append(item)
    for items in strata.values():
        items.sort(key=lambda c: stable_rank(c, seed))
    selected = []
    keys = sorted(strata, key=lambda k: hashlib.sha256(f"{seed}:{k}".encode()).hexdigest())
    while len(selected) < target_frames:
        progressed = False
        for key in keys:
            if strata[key] and len(selected) < target_frames:
                selected.append(strata[key].pop(0))
                progressed = True
        if not progressed:
            break
    return selected


def assign_splits(selected: list[Candidate], seed: str) -> None:
    groups: dict[str, list[Candidate]] = defaultdict(list)
    for item in selected:
        groups[item.group].append(item)
    totals = Counter()
    status_totals = Counter()
    ordered = sorted(
        groups.items(),
        key=lambda pair: (-len(pair[1]), hashlib.sha256(f"{seed}:{pair[0]}".encode()).hexdigest()),
    )
    for _, items in ordered:
        status = items[0].status
        candidates = []
        for split, fraction in SPLIT_TARGETS.items():
            desired_all = len(selected) * fraction
            desired_status = sum(x.status == status for x in selected) * fraction
            score = (totals[split] / max(desired_all, 1)) + (
                status_totals[(split, status)] / max(desired_status, 1)
            )
            candidates.append((score, split))
        split = min(candidates)[1]
        for item in items:
            item.split = split
            totals[split] += 1
            status_totals[(split, item.status)] += 1


def yolo_line(box: dict) -> str:
    x1 = max(0.0, min(1.0, float(box["x1"])))
    y1 = max(0.0, min(1.0, float(box["y1"])))
    x2 = max(0.0, min(1.0, float(box["x2"])))
    y2 = max(0.0, min(1.0, float(box["y2"])))
    return f"0 {(x1+x2)/2:.6f} {(y1+y2)/2:.6f} {x2-x1:.6f} {y2-y1:.6f}"


def coco_for_split(items: list[Candidate]) -> dict:
    images, annotations = [], []
    annotation_id = 1
    for image_id, item in enumerate(sorted(items, key=lambda x: x.frame_id), 1):
        images.append(
            {
                "id": image_id,
                "file_name": f"{item.frame_id}{item.path.suffix.lower()}",
                "width": item.width,
                "height": item.height,
                "captured_at": item.captured_at or None,
                "source": item.source,
                "condition": item.condition,
                "is_hard_negative": item.status == "no_fish",
            }
        )
        for box in item.boxes:
            x1 = max(0.0, min(1.0, float(box["x1"])))
            y1 = max(0.0, min(1.0, float(box["y1"])))
            x2 = max(0.0, min(1.0, float(box["x2"])))
            y2 = max(0.0, min(1.0, float(box["y2"])))
            x, y, w, h = x1 * item.width, y1 * item.height, (x2-x1) * item.width, (y2-y1) * item.height
            annotations.append(
                {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": 1,
                    "bbox": [round(x, 3), round(y, 3), round(w, 3), round(h, 3)],
                    "area": round(w * h, 3),
                    "iscrowd": 0,
                }
            )
            annotation_id += 1
    return {
        "info": {"description": "TalTech Fish vs Drifting Debris Hackathon Dataset", "version": "1.0"},
        "licenses": [{"id": 1, "name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}],
        "categories": [{"id": 1, "name": "fish", "supercategory": "animal"}],
        "images": images,
        "annotations": annotations,
    }


def write_dataset(output: Path, selected: list[Candidate], audit: dict, seed: str) -> dict:
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    (output / "annotations").mkdir(parents=True)
    (output / "metadata").mkdir(parents=True)
    for split in SPLIT_TARGETS:
        (output / "images" / split).mkdir(parents=True)
        (output / "labels" / "yolo" / split).mkdir(parents=True)

    rows = []
    fishbox_annotations = {"schema_version": "1.0", "annotations": {}, "no_fish": [], "splits": {}}
    for item in sorted(selected, key=lambda x: (x.split, x.frame_id)):
        suffix = item.path.suffix.lower()
        image_name = item.frame_id + suffix
        shutil.copy2(item.path, output / "images" / item.split / image_name)
        label = "\n".join(yolo_line(box) for box in item.boxes)
        (output / "labels" / "yolo" / item.split / f"{item.frame_id}.txt").write_text(
            label + ("\n" if label else ""), encoding="utf-8"
        )
        if item.boxes:
            fishbox_annotations["annotations"][item.frame_id] = item.boxes
        else:
            fishbox_annotations["no_fish"].append(item.frame_id)
        fishbox_annotations["splits"][item.frame_id] = item.split
        rows.append(
            {
                "frame_id": item.frame_id,
                "image_file": f"images/{item.split}/{image_name}",
                "split": item.split,
                "project": item.project,
                "source": item.source,
                "captured_at": item.captured_at,
                "date": item.date,
                "hour": item.hour,
                "time_band": item.time_band,
                "status": item.status,
                "annotation_count": item.annotation_count,
                "width": item.width,
                "height": item.height,
                "brightness": f"{item.brightness:.3f}",
                "contrast": f"{item.contrast:.3f}",
                "edge_energy": f"{item.edge_energy:.3f}",
                "brightness_band": item.brightness_band,
                "contrast_band": item.contrast_band,
                "texture_band": item.texture_band,
                "color_cast": item.color_cast,
                "capture_group": item.group,
            }
        )
    with (output / "metadata" / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "annotations" / "fishbox_annotations.json").write_text(
        json.dumps(fishbox_annotations, indent=2, sort_keys=True), encoding="utf-8"
    )
    for split in SPLIT_TARGETS:
        subset = [item for item in selected if item.split == split]
        (output / "annotations" / f"instances_{split}.json").write_text(
            json.dumps(coco_for_split(subset), indent=2), encoding="utf-8"
        )
    stats = summarize(selected)
    build = {
        "dataset_version": "1.0.0",
        "seed": seed,
        "selection_method": "round-robin across project/source/date/time/visual-condition strata",
        "split_method": "capture-source and 10-minute temporal groups; deterministic 70/15/15 allocation",
        "audit": audit,
        "summary": stats,
    }
    (output / "metadata" / "build_report.json").write_text(json.dumps(build, indent=2), encoding="utf-8")
    return build


def summarize(selected: list[Candidate]) -> dict:
    def counts(key):
        return dict(sorted(Counter(key(item) for item in selected).items()))
    by_split = {}
    for split in SPLIT_TARGETS:
        subset = [item for item in selected if item.split == split]
        by_split[split] = {
            "images": len(subset),
            "fish_positive_images": sum(item.status == "fish" for item in subset),
            "hard_negative_images": sum(item.status == "no_fish" for item in subset),
            "fish_boxes": sum(item.annotation_count for item in subset),
        }
    return {
        "images": len(selected),
        "fish_positive_images": sum(item.status == "fish" for item in selected),
        "hard_negative_images": sum(item.status == "no_fish" for item in selected),
        "fish_boxes": sum(item.annotation_count for item in selected),
        "date_range": [min(item.date for item in selected), max(item.date for item in selected)],
        "dates": counts(lambda x: x.date),
        "time_bands": counts(lambda x: x.time_band),
        "projects": counts(lambda x: x.project),
        "sources": counts(lambda x: x.source),
        "brightness_bands": counts(lambda x: x.brightness_band),
        "contrast_bands": counts(lambda x: x.contrast_band),
        "texture_bands": counts(lambda x: x.texture_band),
        "color_casts": counts(lambda x: x.color_cast),
        "splits": by_split,
    }


def write_repo_metadata(repo_metadata: Path, dataset_output: Path, build: dict) -> None:
    repo_metadata.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dataset_output / "metadata" / "manifest.csv", repo_metadata / "selection_manifest.csv")
    shutil.copy2(dataset_output / "metadata" / "build_report.json", repo_metadata / "build_report.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fishbox-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-metadata", type=Path, required=True)
    parser.add_argument("--positive-frames", type=int, default=900)
    parser.add_argument("--negative-frames", type=int, default=300)
    parser.add_argument("--seed", default="taltech-hackathon-v1")
    args = parser.parse_args()
    candidates, audit = load_candidates(args.fishbox_root)
    positives = [item for item in candidates if item.status == "fish"]
    negatives = [item for item in candidates if item.status == "no_fish"]
    selected = diverse_sample(positives, args.positive_frames, args.seed + ":positive")
    selected += diverse_sample(negatives, args.negative_frames, args.seed + ":negative")
    assign_splits(selected, args.seed)
    if sum(item.annotation_count for item in selected) < 1000:
        raise RuntimeError("Selection contains fewer than 1,000 fish box annotations")
    build = write_dataset(args.output, selected, audit, args.seed)
    write_repo_metadata(args.repo_metadata, args.output, build)
    print(json.dumps(build["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
