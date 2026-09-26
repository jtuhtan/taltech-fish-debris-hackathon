# Participant guide

## Goal

Build a proof of concept that finds fish in underwater camera images without
being fooled by leaves, plants, bubbles, sediment, glare, or other noise. Then
show why it matters for rivers and how it could work as a real service.

Your entry is judged on the four official DEEP categories. See
[SCORING.md](SCORING.md) for what judges look for in each.

| DEEP category | Points |
| --- | ---: |
| 🌍 1. Strategic Alignment & Climate Impact | 25 |
| 🛠️ 2. Innovation & Technical Feasibility | 25 |
| 📈 3. Business-Readiness & Scalability | 30 |
| 🎤 4. Team Capabilities & Pitch Quality | 20 |

This guide has one section for each category, followed by the rules that apply
to every team.

## Plan your time

- All four categories count. Categories 3 and 4 together are half of the
  points.
- Get a simple baseline working early. Then work in parallel: some team members
  improve the model while others build the impact story, the business case, and
  the demo.
- Freeze the model before you finish the pitch, so your numbers do not change
  at the last minute.

## 🌍 1. Strategic Alignment & Climate Impact

Underwater cameras help show whether fish passes at hydropower plants and river
barriers really work. Under the EU Water Framework Directive (WFD), rivers must
reach good ecological status, and fish migration past barriers is part of that.
Hydropower supplies renewable electricity, so reliable monitoring helps clean
energy and healthy rivers go together.

The hardest time is high flow. Floods bring turbid water, leaves, branches,
and sediment, so false alarms peak. Many fish also migrate then.

1. **Find your hardest cases.** In `train` and `validation`, look at night,
   low-contrast, and debris-heavy no-fish frames.
2. **Protect fish recall.** Check that fewer false alarms do not come from
   missing fish.
3. **Decide what happens when a scene is unreadable.** For example, flag it for
   human review instead of discarding it.
4. **Link your result to fish-pass evidence.** Explain how your system makes it
   more reliable, continuous, or affordable to show that a fish pass works.

The dataset has no flow, rainfall, or turbidity labels. Use the hardest visual
conditions as a proxy and state clearly what you could not test.

## 🛠️ 2. Innovation & Technical Feasibility

This category is measured with our [benchmark](BENCHMARK.md): model
performance, edge readiness, and reproducibility.

Your model must return a bounding box and a confidence score for each fish it
finds. A frame with no fish should normally return no boxes.

### Technical workflow

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
9. **Submit your predictions.** Upload them with the submission form. See
   [How to submit](#how-to-submit).

### Prediction format

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

### What to report

Report every item below, even if the value is not available. Write `not
measured` rather than leaving a field blank.

Detection quality:

- precision at confidence `0.25` and IoU `0.50`;
- fish recall at confidence `0.25` and IoU `0.50`;
- F2 score at confidence `0.25` and IoU `0.50`;
- false-positive rate on no-fish frames;
- COCO mAP50 and mAP50:95;
- positive-frame recall: the share of fish frames with at least one matched
  fish; and
- results by time band (`dawn`, `day`, `dusk`, `night`) and, if possible, by
  camera source.

Edge readiness:

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
device for the benchmark score.

## 📈 3. Business-Readiness & Scalability

A motion detector can create thousands of false events per station, per day.
Someone has to review them. Your business case starts there.

1. **Pick a target user.** For example: a hydropower operator, a fish-pass
   owner, a water authority, or an environmental consultant. Say who pays.
2. **Estimate review hours saved per station.** Use your measured no-fish
   rejection rate and state every assumption:

   ```text
   review hours saved per station per day ≈
     false events per day × no-fish rejection rate × review seconds per event / 3600
   ```

3. **Sketch the deployment.** For example: camera → edge device → fish events →
   human review. Say what runs offline and what is sent onward.
4. **Choose an operating model.** For example: an edge device, a software
   licence per station, or monitoring as a service.
5. **Explain how it scales.** What does a new station need: hardware, set-up,
   site-specific data or retraining, model updates, and data transfer? What
   would a first pilot at one station look like?

You do not need a finished product. Judges look for a credible path to real
use.

## 🎤 4. Team Capabilities & Pitch Quality

Prepare a short live or recorded demo that shows:

- one fish case;
- one no-fish case; and
- one failure, with what you would improve next.

Build the pitch around the four categories:

1. **Problem and impact:** why missed fish and false alarms matter for rivers.
2. **Evidence:** what you built and how well it works.
3. **Business case:** who uses it, the review hours saved, and how it scales.
4. **Team and next step:** who did what, and what you would do in a pilot.

## How to submit

1. Freeze your system and run it once on the `test` images.
2. Open the [submission form](https://github.com/jtuhtan/taltech-fish-debris-hackathon/issues/new?template=submission.yml).
3. Enter your team name and drag your predictions `.json` file into the
   **Predictions file** box. Add your code URL and submission report if they
   are ready.
4. Confirm the declarations and submit the issue.

Within a few minutes, a GitHub Action checks the file, scores it with the
reference evaluator, and posts the result on your issue. The challenge owners
are notified to review it. Results are provisional until they do.

- If the check finds a format problem, edit the issue and replace the file. It
  is checked again automatically.
- Use the image IDs from `annotations/instances_test.json`. The validation
  split uses the same ID numbers, so validation predictions would be scored
  against the wrong images.
- If you submit more than once, by editing your issue or opening a new one,
  your **latest submission before the deadline** counts. The judges see every
  submission and every edit.
- The repository is public, so your file and score are visible to everyone.

## Minimum submission

Your submission must contain:

- a short `README` with one command or notebook path for inference;
- source code or a runnable notebook;
- frozen model weights, or a public download link;
- test predictions in standard COCO result JSON format, uploaded with the
  submission form;
- a completed report based on [SUBMISSION_TEMPLATE.md](SUBMISSION_TEMPLATE.md),
  covering all four categories;
- a list of pretrained models and outside datasets used;
- a license for your own code; and
- a short live demo or recorded demo.

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

## What makes a strong entry

A strong entry works across all four categories:

- 🌍 it keeps finding fish in the hardest conditions and shows why that matters
  for rivers;
- 🛠️ it catches fish reliably, stays quiet on no-fish frames, runs near the
  camera, and can be reproduced;
- 📈 it saves review time for a clear user and could run at many sites; and
- 🎤 a clear demo and pitch show all of this, including failures, honestly.

A simple working system with clear evidence is better than a large idea that
cannot be tested.

The category 2 benchmark follows useful patterns from related challenges: a
fixed dataset and operating point, as used in
[MLPerf Tiny](https://mlcommons.org/benchmarks/inference-tiny/); and explicit
animal-present and empty-frame evaluation, as in
[iWildCam](https://www.kaggle.com/competitions/iwildcam2018/overview).
