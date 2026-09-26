# Category 2 benchmark

This benchmark measures DEEP category 2, **Innovation & Technical
Feasibility** (25 of the 100 points). It does not decide the overall ranking.
For all four DEEP categories and what judges look for in each, see
[SCORING.md](SCORING.md).

## Summary

The benchmark has three parts. Their points are **relative weights within
category 2**, not points in the overall ranking.

| Part | Benchmark points | What matters |
| --- | ---: | --- |
| Measured model performance | 60 | Finds fish and rejects no-fish frames |
| Edge readiness | 15 | Speed, memory, size, and a credible deployment path |
| Reproducibility | 10 | Judges can understand and run the work |
| **Benchmark total** | **85** | |

A full benchmark score of 85 corresponds to the full 25 points of category 2:

```text
category 2 points = 25 × benchmark points / 85
```

## 1. Measured model performance: 60 benchmark points

All values in the formula are between 0 and 1:

```text
model points =
    25 × fish F2
  + 15 × no-fish rejection rate
  + 10 × COCO mAP50:95
  + 10 × mean time-band F2
```

The fixed scored operating point is confidence `0.25` and IoU `0.50`.

Run the reference evaluator after installing the repository requirements:

```bash
python scripts/evaluate_predictions.py \
  --ground-truth annotations/instances_test.json \
  --predictions predictions.json \
  --manifest metadata/manifest.csv \
  --output results.json
```

The evaluator reports this part as `model_points_out_of_60`.

- **Fish F2 (25):** combines precision and recall, while giving recall more
  weight. Missing a migrating fish is costly.
- **No-fish rejection (15):** the share of reviewed no-fish frames that have no
  prediction at or above the confidence threshold. This directly rewards fewer
  false alarms.
- **COCO mAP50:95 (10):** rewards accurate boxes across IoU thresholds from
  0.50 to 0.95.
- **Mean time-band F2 (10):** calculate F2 separately for dawn, day, dusk, and
  night, then take the unweighted mean over bands present in the test set. This
  rewards performance in different conditions, not only the largest group.

### Box matching

For the fixed operating-point metrics, predictions are sorted by confidence.
One prediction can match one ground-truth fish. A match is a true positive when
its box has IoU of at least `0.50` with an unmatched ground-truth box. Other
predictions are false positives. Unmatched ground-truth boxes are false
negatives.

```text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F2        = 5 × precision × recall / (4 × precision + recall)

no-fish false-positive rate =
  no-fish frames with at least one prediction / all no-fish frames

no-fish rejection rate = 1 - no-fish false-positive rate
```

If a denominator is zero, that metric is zero. The organisers' evaluation is
the official result. Values are kept at full precision for ranking and rounded
only for display.

## 2. Edge readiness: 15 benchmark points

| Item | Points | Full-credit evidence |
| --- | ---: | --- |
| Inference speed | 5 | Reproducible p50 and p95 latency; strong common-device result |
| Model size | 3 | Small deployable package with size reported |
| Memory use | 3 | Peak memory measured and suitable for the proposed device |
| Deployment design | 2 | Clear camera-to-decision flow and offline operation plan |
| Efficiency evidence | 2 | Quantisation, profiling, or energy measurement with no hidden accuracy loss |

Self-measured speed must include the device, runtime, precision, input size, and
batch size. Judges compare speed for ranked finalists on the same available
organiser device when possible. If a common rerun is not possible, speed points
are based on measurement quality and the credibility of the deployment plan,
not a raw comparison between unlike devices.

## 3. Reproducibility: 10 benchmark points

- 4 points: inference runs from clear instructions;
- 2 points: dependencies and model weights are fixed and available;
- 2 points: predictions and reported numbers can be reproduced; and
- 2 points: outside data, pretrained models, training choices, and licences are
  declared.

For judged items in edge readiness and reproducibility, each judge records a
score and the mean is used.

## Tie-breaks within category 2

If two entries have the same benchmark score, rank them within category 2 in
this order:

1. higher no-fish rejection rate;
2. higher fish recall;
3. higher fish F2;
4. lower common-device p95 latency; and
5. final vote of the judging panel.

These tie-breaks apply only to the category 2 benchmark ranking. They do not
decide ties in the overall DEEP ranking.
