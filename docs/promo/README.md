# "Fish or debris?" promo animation

`fish-or-debris.gif` (800 px, shown at the top of the main README) and
`fish-or-debris.mp4` (1920 × 1080, for slides and the challenge lightning talk)
are the same 30-second loop: a three-round "Which frame has a fish?" quiz, a
school of 13 fish, a night frame, and the dataset summary.

Every frame is an unchanged image from the version 1.0.0 training split. The
green boxes are the released fish annotations from
`annotations/instances_train.json`; they are not model predictions.

| Scene | Fish frame | No-fish frame | Source |
| --- | --- | --- | --- |
| Round 1 | `f-218ad4d7cd1d` (1 box) | `f-961b6a879ccc` | EDGE_DEVICE, dusk |
| Round 2 | `f-c76e4c313c73` (1 box) | `f-2b06d6762820` | IAHC2407, dusk |
| Round 3 | `f-a3836e0ae8c1` (1 box) | `f-10e8054729b0` | PIKE, dawn and day |
| School | `f-b8aa32721eb9` (13 boxes) | | PIKE, day |
| Night | `f-7286ed7a14c7` (5 boxes) | | PIKE, night |

The no-fish captions (`dark drifting clumps`, `leaf-like material`, and
`twig-like debris`) describe what is visible. They are not new annotations: the
dataset labels no-fish frames only at frame level.

To regenerate both files from the downloaded dataset (needs `ffmpeg`):

```bash
python scripts/make_promo_video.py --dataset /path/to/taltech-fish-debris-dataset
```

The images are covered by the repository's [dataset licence](../../DATA_LICENSE.md).
The I AM HYDRO and TalTech logos on the final card are described in
[docs/brand](../brand/README.md).
