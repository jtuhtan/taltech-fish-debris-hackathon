# Telling Fish from Drifting Debris in Underwater Monitoring Videos

An open, curated computer-vision dataset for the I AM HYDRO hackathon. It
supports experiments that reduce false triggers in continuous underwater fish
monitoring at fish passages and river barriers.

The dataset contains fish bounding boxes and reviewed hard-negative frames
covering multiple capture dates, times of day, deployments, lighting levels,
contrast levels, texture levels, and underwater color casts. Nearby frames are
kept in the same split to reduce temporal leakage.

Version 1.0.0 contains **1,200 images**, **1,291 fish bounding boxes**, and
**300 reviewed hard-negative frames**. It covers 13 dates from 10 June 2025 to
24 July 2026 and includes dawn, day, dusk, and night imagery.

## Download

The dataset folder is hosted on OneDrive because the image payload is too
large for a regular Git repository. OneDrive can download the complete folder
as a ZIP archive.

**Download link:** _added at publication time_

After downloading, verify files against `SHA256SUMS` in the release folder.

## Task and labels

- `fish`: bounding-box annotation for a visible fish.
- `no_fish`: a reviewed frame-level hard negative, represented by an empty
  YOLO label file. These frames may contain drifting debris, bubbles, sediment,
  changing illumination, or no moving target.

Important: the negative frames have not been subclassified into debris types.
Do not treat them as object-level “debris” annotations.

## Formats

The archive contains:

```text
images/{train,validation,test}/
labels/yolo/{train,validation,test}/
annotations/instances_{train,validation,test}.json
annotations/fishbox_annotations.json
metadata/manifest.csv
metadata/build_report.json
data.yaml
```

COCO and YOLO labels are provided. Bounding boxes are clamped to the image
extent during export. Each `frame_id` is `f-` plus the first 12 hexadecimal
characters of the SHA-256 digest of the complete source image.

## Split policy

The deterministic 70/15/15 split is made by capture source and 10-minute time
window, so adjacent frames do not cross splits. The curation script samples in
round-robin order across project, deployment, date, time band, and coarse
visual-condition strata. See `metadata/build_report.json` for exact counts and
`metadata/selection_manifest.csv` for an auditable row per image.

## Reproduce the curation

With access to the private Fishbox source tree:

```bash
python scripts/build_dataset.py \
  --fishbox-root /home/jeff/fishbox \
  --output /path/to/TalTech-Fish-Debris-Hackathon-v1.0.0 \
  --repo-metadata metadata
```

The source tree and the generated dataset are never modified in place.

## Responsible use and limitations

This dataset is intended for research, education, benchmarking, and prototype
development. Conditions come from a limited number of camera deployments and
should not be assumed to represent every river, species, season, camera, or
hydraulic regime. A model that performs well here still requires site-specific
validation before operational ecological monitoring.

## License

Dataset files are CC BY 4.0; see [DATA_LICENSE.md](DATA_LICENSE.md). Curation
code is MIT-licensed; see [LICENSE](LICENSE).
