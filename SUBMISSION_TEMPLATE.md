# Submission report

Fill in one section for each of the four DEEP judging categories. See
[SCORING.md](SCORING.md) for what judges look for.

## Team

- Team name:
- Members:
- Contact:
- Project title:
- Code URL:
- Model download URL:
- Demo URL, if used:

## One-sentence result

What did you build, and why is it useful?

## 🌍 1. Strategic Alignment & Climate Impact

- How the system behaves on debris-heavy, low-contrast, or night frames, as a
  proxy for floods and high flow:
- How it protects fish recall during migration peaks:
- What it does when a scene is unreadable:
- How it helps show that a fish pass works, for example for the EU Water
  Framework Directive:
- What we could not test with this dataset:

## 🛠️ 2. Innovation & Technical Feasibility

- What is new or different in our approach:

### Method

- Model and version:
- Pretrained weights:
- Outside datasets:
- Input size:
- Training changes:
- Confidence threshold: 0.25
- Post-processing:
- Numeric precision or quantisation:

### Detection results

| Metric | Validation | Test |
| --- | ---: | ---: |
| Precision at IoU 0.50 | | |
| Fish recall at IoU 0.50 | | |
| F2 at IoU 0.50 | | |
| No-fish false-positive rate | | |
| No-fish rejection rate | | |
| COCO mAP50 | | |
| COCO mAP50:95 | | |
| Positive-frame recall | | |
| Dawn F2 | | |
| Day F2 | | |
| Dusk F2 | | |
| Night F2 | | |

### Edge results

| Item | Result |
| --- | --- |
| Model file size | |
| Input image size | |
| p50 latency, batch 1 | |
| p95 latency, batch 1 | |
| Frames per second, batch 1 | |
| Peak RAM or device memory | |
| Energy per image, if measured | |
| Test hardware | |
| Operating system | |
| Runtime and version | |
| CPU, GPU, or NPU precision | |
| Training time and hardware | |

### Reproduce our result

Give the shortest complete setup and inference instructions. State the expected
output path and format.

```bash
# Add commands here
```

## 📈 3. Business-Readiness & Scalability

- Target users and who pays:
- Estimated review hours saved per station per day, with assumptions:
- Deployment (camera to decision) and operating model (edge device, licence,
  or service):
- What a new site needs, and how it scales to many sites:
- What a first pilot would look like:

## 🎤 4. Team Capabilities & Pitch Quality

- Who did what, and the skills we bring to a pilot:
- Fish demo case:
- No-fish demo case:
- Failure case, and what we would improve next:
- What does not work yet:

## Licences and declarations

- Code licence:
- Model licence:
- Outside data licences:
- We did not train on, tune on, manually relabel, or select settings from the
  test labels: yes / no
- Other information judges should know:
