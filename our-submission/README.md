# DeepVision — Fish vs Debris Detection

Team submission for the I AM HYDRO / TalTech challenge, EIT Water Hackathon Munich 2026.

## What's here

- `submission/` — training, inference, and evaluation scripts, plus the frozen model and results
- `webapp/` — a local FastAPI + HTML demo site (live detector, real-results gallery, ROI calculator, roadmap)

## Model

YOLOv8n (Ultralytics), pretrained on COCO, fine-tuned for 20 epochs on the official dataset
(840 train / 180 val / 180 test images, single class: `fish`). Outside data/models used: COCO
pretrained weights via `ultralytics`, no other outside data.

Frozen weights: `submission/runs/fish_yolov8n_e20/weights/best.pt`

## Results (test split, official operating point: confidence 0.25, IoU 0.50)

See `submission/results_e20.json` for full numbers (produced by the organizers' own
`scripts/evaluate_predictions.py`). Headline:

- Fish F2: 0.809 · Precision: 0.854 · Recall: 0.799
- No-fish rejection rate: 97.8%
- COCO mAP50 / mAP50-95: 0.852 / 0.595
- Model size: 5.97 MB · p50/p95 latency: 18.4ms / 27.7ms (Apple M4, MPS, fp32, batch 1)

## How to run inference

```bash
pip install ultralytics
python submission/predict_test.py --weights submission/runs/fish_yolov8n_e20/weights/best.pt --output predictions.json
```

## How to reproduce training

```bash
python submission/train.py --epochs 20 --imgsz 832 --device mps
```

## How to run the demo site

```bash
pip install fastapi uvicorn python-multipart ultralytics
cd webapp/backend
uvicorn main:app --port 8000
```
Then open `http://localhost:8000`.

## Known limitation

Night-time recall (0.65) is meaningfully lower than day (0.91) — see `submission/results_e20.json`
`time_bands` for the full breakdown. This is the model's clearest weak point and the top priority
for future work.
