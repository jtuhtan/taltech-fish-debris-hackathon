# Judging and scoring

Every eligible entry is scored out of 100 points. The same rules apply to every
team.

## Score summary

| Area | Points | What matters |
| --- | ---: | --- |
| Measured model performance | 60 | Finds fish and rejects no-fish frames |
| Edge readiness | 15 | Speed, memory, size, and a credible deployment path |
| Reproducibility | 10 | Judges can understand and run the work |
| Real-world value | 10 | Useful, feasible, and thoughtful solution |
| Demo and explanation | 5 | Clear evidence, limitations, and next steps |
| **Total** | **100** | |

## 1. Measured model performance: 60 points

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

- **Fish F2 (25 points):** combines precision and recall, while giving recall
  more weight. Missing a migrating fish is costly.
- **No-fish rejection (15 points):** the share of reviewed no-fish frames that
  have no prediction at or above the confidence threshold. This directly
  rewards fewer false alarms.
- **COCO mAP50:95 (10 points):** rewards accurate boxes across IoU thresholds
  from 0.50 to 0.95.
- **Mean time-band F2 (10 points):** calculate F2 separately for dawn, day,
  dusk, and night, then take the unweighted mean over bands present in the test
  set. This rewards performance in different conditions, not only the largest
  group.

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

## 2. Edge readiness: 15 points

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

## 3. Reproducibility: 10 points

- 4 points: inference runs from clear instructions;
- 2 points: dependencies and model weights are fixed and available;
- 2 points: predictions and reported numbers can be reproduced; and
- 2 points: outside data, pretrained models, training choices, and licences are
  declared.

## 4. Real-world value: 10 points

- 4 points: likely to reduce manual review while protecting fish recall;
- 3 points: feasible for real river cameras and changing conditions; and
- 3 points: useful or original idea supported by working evidence.

## 5. Demo and explanation: 5 points

- 2 points: clear working demo;
- 1 point: shows a fish example;
- 1 point: shows a no-fish example; and
- 1 point: explains one failure and the next improvement.

## Tie-breaks

If total scores are equal, use this order:

1. higher no-fish rejection rate;
2. higher fish recall;
3. higher fish F2;
4. lower common-device p95 latency; and
5. final vote of the judging panel.

## Judge process

1. Check eligibility and required files.
2. Run the prediction evaluator on the fixed test set.
3. Re-run finalist inference on a common device when practical.
4. Review reproducibility, edge readiness, and real-world value.
5. Watch the demo and ask short questions.
6. Record each judge's rubric scores. Use the mean for judged sections.
7. Add the measured model points and apply the tie-break rules if needed.

Judges must declare conflicts of interest and should not score a team where a
conflict could affect impartiality. The organisers may publish the leaderboard,
metric values, and short judging notes.
