# README example images

These files are unchanged copies from the version 1.0.0 training split. They
are kept in this repository so the main README can show the problem before a
participant downloads the full archive.

| Repository file | Dataset frame | Review status | Source | Capture time band |
| --- | --- | --- | --- | --- |
| `fish-school.png` | `f-b8aa32721eb9` | `fish` (13 boxes) | PIKE | day |
| `fish-single.png` | `f-25a19a323285` | `fish` (1 box) | EDGE_DEVICE | day |
| `fish-single-prediction.png` | derived presentation copy of `f-25a19a323285` | example box and illustrative score | EDGE_DEVICE | day |
| `leaf-like-debris.png` | `f-2b06d6762820` | `no_fish` | IAHC2407 | dusk |
| `suspended-particles.png` | `f-31a522168564` | `no_fish` | PIKE | dawn |

`leaf-like` and `suspended particles` are visual descriptions, not new
annotations. The dataset does not provide object-level debris classes.

`fish-single-prediction.png` is used only to explain expected model output. It
adds a box based on the frame's ground-truth annotation and the illustrative
confidence label `fish 0.91`; confidence scores are not part of the dataset.

The images are covered by the repository's [dataset licence](../../DATA_LICENSE.md).
