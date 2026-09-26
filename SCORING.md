# Judging and scoring

The overall hackathon ranking is decided by the official **DEEP judging
criteria** for the EIT Water Hackathon Munich 2026. The same rules apply to
every team.

This page explains the four DEEP categories, how our fish-debris benchmark
measures category 2, and what the challenge owners look for in the other three.

## Overall ranking: DEEP criteria

| # | DEEP category | Points | In this challenge |
| ---: | --- | ---: | --- |
| 1 | Strategic Alignment & Climate Impact | 25 | Reliable fish monitoring during floods and high flow; evidence that fish passes work |
| 2 | Innovation & Technical Feasibility | 25 | Our benchmark: model performance, edge readiness, and reproducibility |
| 3 | Business-Readiness & Scalability | 30 | Review hours saved, scaling to many sites, and a credible operating model |
| 4 | Team Capabilities & Pitch Quality | 20 | Clear working demo, honest evidence, and a convincing pitch |
| | **Total** | **100** | |

> [!IMPORTANT]
> Model performance is not the overall score. It is the largest part of
> category 2, which is 25 of the 100 points. Business-Readiness & Scalability
> is the largest category.

## Category 1: Strategic Alignment & Climate Impact

What we look for:

- **Robust during floods and high flow.** High flow brings turbid water,
  leaves, branches, and sediment, so false alarms peak. Many fish also migrate
  during high flow. A system that fails or is switched off then misses the
  events that matter most. Show how your system behaves on debris-heavy,
  low-contrast, and night frames, and what it does when a scene becomes
  unreadable.
- **Protects fish recall.** Fewer false alarms must not come from missing fish.
- **Links to the EU Water Framework Directive (WFD).** Rivers must reach good
  ecological status, and fish migration past barriers is part of that. Operators
  and authorities need evidence that fish passes really work. Explain how your
  system makes that evidence more reliable, continuous, or affordable.

The dataset has no flow, rainfall, or turbidity labels. Use the hardest visual
conditions as a proxy and state clearly what you could not test.

## Category 2: Innovation & Technical Feasibility — our benchmark

Our benchmark measures category 2. It has three parts. Their points are
**relative weights within category 2**, not points in the overall ranking.

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

### 2a. Measured model performance: 60 benchmark points

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

#### Box matching

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

### 2b. Edge readiness: 15 benchmark points

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

### 2c. Reproducibility: 10 benchmark points

- 4 points: inference runs from clear instructions;
- 2 points: dependencies and model weights are fixed and available;
- 2 points: predictions and reported numbers can be reproduced; and
- 2 points: outside data, pretrained models, training choices, and licences are
  declared.

### Tie-breaks within category 2

If two entries have the same benchmark score, rank them within category 2 in
this order:

1. higher no-fish rejection rate;
2. higher fish recall;
3. higher fish F2;
4. lower common-device p95 latency; and
5. final vote of the judging panel.

These tie-breaks apply only to the category 2 benchmark ranking. They do not
decide ties in the overall DEEP ranking.

## Category 3: Business-Readiness & Scalability

What we look for:

- **Review hours saved per station.** Estimate how much manual review your
  system removes while keeping fish recall. State every assumption, for
  example:

  ```text
  review hours saved per station per day ≈
    false events per day × no-fish rejection rate × review seconds per event / 3600
  ```

- **Scaling to many sites.** Explain what a new station needs: hardware,
  set-up, site-specific data or retraining, model updates, and data transfer.
- **A credible operating model.** Say who uses it, who pays, and how: for
  example, an edge device, a software licence per station, or monitoring as a
  service.

## Category 4: Team Capabilities & Pitch Quality

What we look for:

- a clear working demo;
- a fish example;
- a no-fish example;
- one failure explained, with the next improvement;
- a pitch that covers the problem, the evidence, the impact, and the business
  case in the time given; and
- a team that can credibly take the next step, such as a pilot at one station.

## Judge process

1. Check eligibility and required files.
2. Run the prediction evaluator on the fixed test set.
3. Re-run finalist inference on a common device when practical.
4. Score edge readiness and reproducibility. Record each judge's scores and use
   the mean. Add the measured model points to get the benchmark score for
   category 2, and apply the category 2 tie-breaks if needed.
5. Watch the demo and pitch, and ask short questions.
6. Score categories 1, 3, and 4 using the DEEP criteria.
7. Rank all entries by their total DEEP score out of 100.

Judges must declare conflicts of interest and should not score a team where a
conflict could affect impartiality. The organisers may publish the benchmark
leaderboard, metric values, and short judging notes.
