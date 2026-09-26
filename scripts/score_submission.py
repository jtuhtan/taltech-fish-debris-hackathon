#!/usr/bin/env python3
"""Score a test-set submission from a GitHub issue and write a results comment."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALUATOR = REPO_ROOT / "scripts" / "evaluate_predictions.py"
GROUND_TRUTH_NAME = "annotations/instances_test.json"
GROUND_TRUTH_ENV = "TEST_GROUND_TRUTH_GZ_B64"
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
MAX_PREDICTIONS = 100_000
MAX_ERRORS = 10
EVENT_TIMEZONE = ZoneInfo("Europe/Berlin")
ATTACHMENT_URL = re.compile(
    r"https://github\.com/(?:user-attachments/files|[\w.-]+/[\w.-]+/files)"
    r"/\d+/[^\s()\[\]<>\"'`]+(?i:\.json)"
)
BENCHMARK_NOTE = (
    "> This is the model-performance part of the category 2 benchmark. Edge "
    "readiness and reproducibility are scored by the judges, and the overall "
    "ranking uses all four DEEP categories. Results are provisional until the "
    "challenge owners review them. If a team submits more than once, its latest "
    "submission before the deadline counts."
)


class SubmissionError(Exception):
    """A problem the team can fix by replacing the file."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", required=True, type=Path, help="gh issue view --json output")
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--comment", required=True, type=Path, help="Markdown comment output path")
    parser.add_argument("--predictions", type=Path, help="Use a local file instead of the attachment")
    parser.add_argument(
        "--ground-truth",
        type=Path,
        help=f"Test annotations; defaults to the gzip+base64 value of ${GROUND_TRUTH_ENV}",
    )
    parser.add_argument("--manifest", type=Path, default=REPO_ROOT / "metadata" / "selection_manifest.csv")
    parser.add_argument("--checksums", type=Path, default=REPO_ROOT / "metadata" / "SHA256SUMS")
    parser.add_argument("--reviewers", default=os.environ.get("RESULTS_REVIEWERS", ""))
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.50)
    return parser.parse_args()


def issue_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for section in re.split(r"(?m)^### ", body or "")[1:]:
        label, _, value = section.partition("\n")
        value = value.strip()
        fields[label.strip()] = "" if value == "_No response_" else value
    return fields


def attachment_url(fields: dict[str, str], body: str) -> str:
    text = fields.get("Predictions file", body or "")
    urls = list(dict.fromkeys(ATTACHMENT_URL.findall(text)))
    if not urls:
        raise SubmissionError(
            "No `.json` attachment was found. Drag and drop your predictions file "
            "into the **Predictions file** box so GitHub uploads it."
        )
    if len(urls) > 1:
        raise SubmissionError("Attach exactly one `.json` predictions file.")
    return urls[0]


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "taltech-fish-debris-scorer"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(MAX_DOWNLOAD_BYTES + 1)
    except OSError as exc:
        raise SubmissionError(f"The attachment could not be downloaded ({exc}). Try attaching it again.") from exc
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise SubmissionError("The file is larger than 25 MB.")
    destination.write_bytes(data)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_checksum(checksums: Path, name: str) -> str:
    for line in checksums.read_text(encoding="utf-8").splitlines():
        digest, _, path = line.partition("  ")
        if path.strip() == name:
            return digest.strip()
    raise RuntimeError(f"{name} is not listed in {checksums}.")


def load_ground_truth(args: argparse.Namespace, destination: Path) -> Path | None:
    if args.ground_truth:
        path = args.ground_truth
    else:
        encoded = os.environ.get(GROUND_TRUTH_ENV, "").strip()
        if not encoded:
            return None
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(gzip.decompress(base64.b64decode(encoded)))
        path = destination
    expected = expected_checksum(args.checksums, GROUND_TRUTH_NAME)
    if sha256(path) != expected:
        raise RuntimeError(f"Ground truth does not match the published SHA-256 for {GROUND_TRUTH_NAME}.")
    return path


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def code(value: Any, limit: int = 40) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = text.replace("`", "'").replace("\n", " ")
    return f"`{text[:limit]}{'…' if len(text) > limit else ''}`"


def check_predictions(path: Path, image_ids: set[int] | None, confidence: float) -> dict[str, int]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SubmissionError(f"The file is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise SubmissionError("The file must contain a JSON list of predictions in COCO result format.")
    if len(data) > MAX_PREDICTIONS:
        raise SubmissionError(f"The file has {len(data):,} predictions; the limit is {MAX_PREDICTIONS:,}.")

    errors: list[str] = []
    for index, item in enumerate(data):
        where = f"Prediction {index}"
        if not isinstance(item, dict):
            errors.append(f"{where} is not a JSON object.")
        else:
            image_id = item.get("image_id")
            if not is_number(image_id) or not float(image_id).is_integer():
                errors.append(f"{where} has image_id {code(image_id)}; it must be an integer.")
            elif image_ids is not None and int(image_id) not in image_ids:
                errors.append(f"{where} has image_id {code(image_id)}, which is not in `{GROUND_TRUTH_NAME}`.")
            if item.get("category_id", 1) != 1:
                errors.append(f"{where} has category_id {code(item.get('category_id'))}; use `1` (fish).")
            bbox = item.get("bbox")
            if (
                not isinstance(bbox, list)
                or len(bbox) != 4
                or not all(is_number(value) for value in bbox)
                or bbox[2] < 0
                or bbox[3] < 0
            ):
                errors.append(f"{where} has bbox {code(bbox)}; use `[x, y, width, height]` in pixels.")
            score = item.get("score")
            if not is_number(score) or not 0 <= score <= 1:
                errors.append(f"{where} has score {code(score)}; it must be a number from 0 to 1.")
        if len(errors) >= MAX_ERRORS:
            errors.append("More problems may follow; only the first ones are shown.")
            break
    if errors:
        raise SubmissionError("The file has format problems:\n\n" + "\n".join(f"- {e}" for e in errors))

    return {
        "predictions": len(data),
        "at_or_above_threshold": sum(1 for item in data if item["score"] >= confidence),
        "images_with_predictions": len({int(item["image_id"]) for item in data}),
    }


def evaluate(args: argparse.Namespace, ground_truth: Path, predictions: Path, output: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(EVALUATOR),
            "--ground-truth", str(ground_truth),
            "--predictions", str(predictions),
            "--manifest", str(args.manifest),
            "--confidence", str(args.confidence),
            "--iou", str(args.iou),
            "--output", str(output),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().splitlines()[-5:]
        raise SubmissionError("The evaluator rejected the file:\n\n" + "\n".join(f"- {code(line, 200)}" for line in detail))
    return json.loads(output.read_text(encoding="utf-8"))


def plain(text: str, limit: int = 100) -> str:
    text = " ".join(text.split())[:limit]
    text = re.sub(r"([\\`*_\[\]<>|#!~])", r"\\\1", text)
    return text.replace("@", "@\u200b")


def event_time(moment: datetime | None) -> str:
    if moment is None:
        return "unknown"
    local = moment.astimezone(EVENT_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    return f"{local} Munich time ({moment.astimezone(timezone.utc):%H:%M:%S} UTC)"


def parse_time(timestamp: str | None) -> datetime | None:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else None


def header(issue: dict[str, Any], fields: dict[str, str], args: argparse.Namespace) -> list[str]:
    team = plain(fields.get("Team name", "")) or "not given"
    author = (issue.get("author") or {}).get("login", "unknown")
    submitted = event_time(parse_time(issue.get("lastEditedAt") or issue.get("createdAt")))
    now = event_time(datetime.now(timezone.utc))
    return [
        f"- **Team:** {team} (submitted by @\u200b{author})",
        f"- **Submitted:** {submitted}, when this issue was created or last edited",
        f"- **Checked:** {now}, confidence `{args.confidence:.2f}` and IoU `{args.iou:.2f}`",
    ]


def results_comment(lines: list[str], result: dict[str, Any], stats: dict[str, int], digest: str, total_images: int) -> list[str]:
    bands = result.get("time_bands", {})
    band_text = " · ".join(f"{band} {values['f2']:.3f}" for band, values in bands.items()) or "not available"
    rows = [
        ("Fish F2", result["f2"]),
        ("Fish precision", result["precision"]),
        ("Fish recall", result["recall"]),
        ("No-fish rejection rate", result["no_fish_rejection_rate"]),
        ("COCO mAP50:95", result["coco_map_50_95"]),
        ("COCO mAP50", result["coco_map_50"]),
        ("Mean time-band F2", result["mean_time_band_f2"]),
        ("Positive-frame recall", result["positive_frame_recall"]),
    ]
    return [
        "## 🏁 Submission scored",
        "",
        *lines,
        f"- **File:** SHA-256 `{digest[:16]}…`, {stats['predictions']:,} predictions "
        f"({stats['at_or_above_threshold']:,} at or above the threshold) on "
        f"{stats['images_with_predictions']} of {total_images} test images",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        *(f"| {name} | {value:.3f} |" for name, value in rows),
        f"| **Model performance points** | **{result['model_points_out_of_60']:.2f} / 60** |",
        "",
        f"Time-band F2: {band_text}",
        "",
        BENCHMARK_NOTE,
        "",
        "<details><summary>Full evaluator output</summary>",
        "",
        "```json",
        json.dumps(result, indent=2, sort_keys=True),
        "```",
        "",
        "</details>",
    ]


def main() -> None:
    args = parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    issue = json.loads(args.issue.read_text(encoding="utf-8"))
    body = issue.get("body") or ""
    fields = issue_fields(body)
    lines = header(issue, fields, args)
    predictions = args.workdir / "predictions.json"
    status = "error"

    try:
        if args.predictions:
            predictions.write_bytes(args.predictions.read_bytes())
        else:
            download(attachment_url(fields, body), predictions)
        ground_truth = load_ground_truth(args, args.workdir.parent / "ground-truth" / "instances_test.json")
        if ground_truth is None:
            stats = check_predictions(predictions, None, args.confidence)
            status = "not-configured"
            comment = [
                "## ⏳ Submission received",
                "",
                *lines,
                "",
                f"The file passed the basic format check ({stats['predictions']:,} predictions), "
                "but scoring is not set up yet. The challenge owners will score it and reply here.",
            ]
        else:
            gt = json.loads(ground_truth.read_text(encoding="utf-8"))
            image_ids = {int(image["id"]) for image in gt["images"]}
            stats = check_predictions(predictions, image_ids, args.confidence)
            result = evaluate(args, ground_truth, predictions, args.workdir / "results.json")
            status = "scored"
            comment = results_comment(lines, result, stats, sha256(predictions), len(image_ids))
    except SubmissionError as exc:
        status = "needs-fix"
        comment = [
            "## ❌ Submission needs a fix",
            "",
            *lines,
            "",
            str(exc),
            "",
            "Edit this issue and replace the file. It will be checked again automatically.",
        ]
    except Exception as exc:  # noqa: BLE001 - report any scoring failure on the issue
        comment = [
            "## ⚠️ Submission could not be scored automatically",
            "",
            *lines,
            "",
            f"The scorer failed with {code(type(exc).__name__)}. The challenge owners will check it.",
        ]
        print(f"Scoring failed: {exc!r}", file=sys.stderr)

    reviewers = " ".join(args.reviewers.split())
    if reviewers and status != "needs-fix":
        comment += ["", f"cc {reviewers} for final results review"]
    args.comment.write_text("\n".join(comment) + "\n", encoding="utf-8")
    print(f"status={status}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"status={status}\n")


if __name__ == "__main__":
    main()
