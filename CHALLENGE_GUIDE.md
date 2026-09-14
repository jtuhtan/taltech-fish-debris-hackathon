# Participant guide

## Goal

Build a proof of concept that finds fish in underwater camera images without
being fooled by leaves, plants, bubbles, sediment, glare, or other noise.

Your model must return a bounding box and a confidence score for each fish it
finds. A frame with no fish should normally return no boxes.

## Suggested workflow

1. **Download and check the data.** Download the OneDrive folder linked in the
   [README](README.md). Check its files with `metadata/SHA256SUMS`.
2. **Explore the labels.** View positive and negative frames. Note changes in
   camera, date, time of day, light, water clarity, fish size, and background.
3. **Choose a baseline.** A small pretrained object detector is a practical
   starting point. Record its first validation result before making changes.
4. **Train only on `train`.** You may use pretrained weights. State all outside
   data and models that you use.
5. **Improve with `validation`.** Try changes such as augmentation, input size,
   confidence threshold, hard-negative training, or model quantization. Do not
   choose settings from the test result.
6. **Freeze the system.** Fix the model, input size, confidence threshold, and
   all post-processing before the final test run.
7. **Run the final test once.** Save predictions in COCO result format. Use the
   fixed confidence threshold of `0.25` for the scored operating point.
8. **Measure edge readiness.** Measure latency, memory, and model size. State
   exactly which hardware and software you used.
9. **Prepare a short demo.** Show at least one fish case, one no-fish case, one
   failure, and what you would improve next.
10. **Submit a reproducible package.** Include code, predictions, weights or a
    download link, environment instructions, and a completed copy of
    [SUBMISSION_TEMPLATE.md](SUBMISSION_TEMPLATE.md).

## Minimum submission

Your submission must contain:

- a short `README` with one command or notebook path for inference;
- source code or a runnable notebook;
- frozen model weights, or a public download link;
- test predictions in standard COCO result JSON format;
- a completed results report based on [SUBMISSION_TEMPLATE.md](SUBMISSION_TEMPLATE.md);
- a list of pretrained models and outside datasets used;
- a license for your own code; and
- a short live demo or recorded demo.

Each prediction is one JSON object:

```json
{
  "image_id": 42,
  "category_id": 1,
  "bbox": [120.5, 80.0, 64.0, 28.5],
  "score": 0.87
}
```

`bbox` is `[x, y, width, height]` in pixels. Put the objects in a JSON list.
Use the image and category IDs from `annotations/instances_test.json`.

## Fair-use rules

- Train on the training split and tune on the validation split.
- Do not inspect test labels, train on them, or select settings from them.
- Pretrained weights and outside data are allowed, but must be declared.
- Do not label the test images yourself or obtain matching frames from another
  copy of the source video.
- The judges may ask for a clean rerun or inspect the code and logs.
- Follow the dataset licence and give credit to TalTech.

Breaking these rules can make an entry ineligible for the ranked awards. A
useful but ineligible prototype may still be shown as an exhibition entry.

## What to report

Report every item below, even if the value is not available. Write `not
measured` rather than leaving a field blank.

### Detection quality

- precision at confidence `0.25` and IoU `0.50`;
- fish recall at confidence `0.25` and IoU `0.50`;
- F2 score at confidence `0.25` and IoU `0.50`;
- false-positive rate on no-fish frames;
- COCO mAP50 and mAP50:95;
- positive-frame recall: the share of fish frames with at least one matched
  fish; and
- results by time band (`dawn`, `day`, `dusk`, `night`) and, if possible, by
  camera source.

### Edge readiness

- model file size in MB;
- input image size;
- median (p50) and p95 latency per image;
- frames per second for batch size 1;
- peak RAM or device memory;
- hardware, operating system, runtime, numeric precision, and batch size;
- training time and training hardware; and
- energy per image if you can measure it. Energy is useful evidence but is not
  required for eligibility.

Latency from different devices is not directly comparable. Teams must provide
self-measured results, and the organisers may rerun finalists on one common
device for the ranked score.

## What makes a strong entry

A strong entry catches fish reliably, stays quiet on no-fish frames, runs fast
enough for an edge camera, and can be reproduced by another team. It also
explains failures honestly. A simple working system with clear evidence is
better than a large idea that cannot be tested.

The structure follows useful patterns from related challenges: a fixed dataset
and operating point, as used in
[MLPerf Tiny](https://mlcommons.org/benchmarks/inference-tiny/); explicit
animal-present and empty-frame evaluation, as in
[iWildCam](https://www.kaggle.com/competitions/iwildcam2018/overview); and a
mix of technical quality, impact, feasibility, and presentation, similar to
the [US Federal AI Hackathon judging criteria](https://gsa-stg-ecas.gsa.gov/technology/government-it-initiatives/federal-ai-hackathon/the-judging).
