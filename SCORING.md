# Judging and scoring

The overall hackathon ranking is decided by the official **DEEP judging
criteria** for the EIT Water Hackathon Munich 2026. Every team is judged on the
same four categories, and all four count.

| DEEP category | Points | Judges ask |
| --- | ---: | --- |
| 🌍 1. Strategic Alignment & Climate Impact | **25** | Does it help protect fish and rivers, even in floods and high flow? |
| 🛠️ 2. Innovation & Technical Feasibility | **25** | Does it work near the camera, and can others reproduce it? |
| 📈 3. Business-Readiness & Scalability | **30** | Who uses it, how much review time does it save, and how does it scale? |
| 🎤 4. Team Capabilities & Pitch Quality | **20** | Can the team show it working and take it further? |
| **Total** | **100** | |

> [!IMPORTANT]
> A strong model alone covers only part of category 2. Business-Readiness &
> Scalability is the largest category, and categories 3 and 4 together are half
> of the points. Plan your time across all four.

## 🌍 1. Strategic Alignment & Climate Impact — 25 points

**Judges ask:** Does this help protect fish and rivers, and does it still work
when it matters most?

What strong entries show:

- **Robustness during floods and high flow.** High flow brings turbid water,
  leaves, branches, and sediment, so false alarms peak. Many fish also migrate
  during high flow. A system that fails or is switched off then misses the
  events that matter most. Show how your system behaves on debris-heavy,
  low-contrast, and night frames, and what it does when a scene becomes
  unreadable.
- **Protected fish recall.** Fewer false alarms must not come from missing
  fish.
- **A link to the EU Water Framework Directive (WFD).** Rivers must reach good
  ecological status, and fish migration past barriers is part of that.
  Operators and authorities need evidence that fish passes really work. Explain
  how your system makes that evidence more reliable, continuous, or affordable.
- **A link to clean energy.** Hydropower supplies renewable electricity, but
  barriers block fish migration. Reliable monitoring helps show that
  renewable power and healthy rivers can go together.

The dataset has no flow, rainfall, or turbidity labels. Use the hardest visual
conditions as a proxy and state clearly what you could not test.

## 🛠️ 2. Innovation & Technical Feasibility — 25 points

**Judges ask:** Does it work, can it run near the camera, and can someone else
reproduce it?

This category is measured with our benchmark. Its three parts are weighted
within category 2:

| Benchmark part | Weight | What matters |
| --- | ---: | --- |
| Measured model performance | 60 | Finds fish and rejects no-fish frames |
| Edge readiness | 15 | Speed, memory, size, and a credible deployment path |
| Reproducibility | 10 | Judges can understand and run the work |

```text
category 2 points = 25 × benchmark points / 85
```

What strong entries show:

- high fish recall and few false alarms at the fixed operating point,
  confidence `0.25` and IoU `0.50`;
- steady results across dawn, day, dusk, and night;
- a small, fast model measured on a named device; and
- a package that another person can run, with all outside data and
  pretrained models declared.

**[Read the full benchmark: formula, evaluator, edge and reproducibility rubrics, and tie-breaks →](BENCHMARK.md)**

## 📈 3. Business-Readiness & Scalability — 30 points

**Judges ask:** Who would use this, how much review time does it save, and how
does it grow from one station to many?

What strong entries show:

- **A clear target user**, for example a hydropower operator, fish-pass owner,
  water authority, or environmental consultant, and who pays.
- **Review hours saved per station.** Estimate how much manual review your
  system removes while keeping fish recall. State every assumption, for
  example:

  ```text
  review hours saved per station per day ≈
    false events per day × no-fish rejection rate × review seconds per event / 3600
  ```

- **Scaling to many sites.** Explain what a new station needs: hardware,
  set-up, site-specific data or retraining, model updates, and data transfer.
- **A credible operating model**, for example an edge device, a software
  licence per station, or monitoring as a service.
- **A realistic next step**, such as a pilot at one station.

This is a proof of concept, not a finished product. Judges look for a credible
path to real use.

## 🎤 4. Team Capabilities & Pitch Quality — 20 points

**Judges ask:** Can this team show it working, explain it clearly, and take it
further?

What strong entries show:

- a clear working demo;
- a fish example and a no-fish example;
- one failure explained, with the next improvement;
- a pitch that covers all four categories in the time given: the problem and
  impact, the evidence, the business case, and the next step; and
- who in the team did what, and the skills the team brings to a pilot.

## Judge process

1. Check eligibility and required files.
2. Measure category 2 with the [benchmark](BENCHMARK.md): review the
   automatic evaluator result on each submission issue, re-run finalist
   inference on a common device when practical, and score edge readiness and
   reproducibility.
3. Watch the demo and pitch, and ask short questions.
4. Score categories 1, 3, and 4 using the DEEP criteria.
5. Rank all entries by their total DEEP score out of 100.

Judges must declare conflicts of interest and should not score a team where a
conflict could affect impartiality. The organisers may publish the benchmark
leaderboard, metric values, and short judging notes.
