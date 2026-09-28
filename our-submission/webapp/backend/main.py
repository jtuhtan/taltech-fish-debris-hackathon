#!/usr/bin/env python3
"""Local demo server for the hackathon pitch. Real model, real dataset results.

Run: uvicorn main:app --reload --port 8000  (from webapp/backend/)
Open: http://localhost:8000
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import inference

BACKEND_DIR = Path(__file__).resolve().parent
WEBAPP_DIR = BACKEND_DIR.parent
FRONTEND_DIR = WEBAPP_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"
DATA_DIR = BACKEND_DIR / "data"
UPLOADS_DIR = WEBAPP_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

DATASET_TEST_IMAGES = Path(
    "/Users/hinata_shoyo/Desktop/ETH/Data/TalTech-Fish-Debris-Hackathon-v1.0.0/images/test"
)
RESULTS_PATH = Path("/Users/hinata_shoyo/Desktop/ETH/submission/results_e20.json")

app = FastAPI(title="Underwater Fish Detection — Live Demo")
app.mount("/test_images", StaticFiles(directory=str(DATASET_TEST_IMAGES)), name="test_images")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

PAGES = {
    "": "home.html",
    "detector": "detector.html",
    "insights": "insights.html",
    "game": "game.html",
    "impact": "impact.html",
    "roadmap": "roadmap.html",
    "tech": "tech.html",
}
for route, filename in PAGES.items():
    def make_handler(fname: str):
        def handler() -> FileResponse:
            return FileResponse(str(PAGES_DIR / fname))
        return handler

    app.get(f"/{route}")(make_handler(filename))


@app.get("/api/gallery")
def gallery() -> JSONResponse:
    data = json.loads((DATA_DIR / "gallery.json").read_text())
    return JSONResponse(data)


@app.get("/api/game")
def game() -> JSONResponse:
    data = json.loads((DATA_DIR / "game.json").read_text())
    return JSONResponse(data)


@app.get("/api/metrics")
def metrics() -> JSONResponse:
    real = json.loads(RESULTS_PATH.read_text()) if RESULTS_PATH.exists() else {}
    real["model_size_mb"] = 5.97
    real["latency_p50_ms"] = 18.4
    real["latency_p95_ms"] = 27.7
    real["fps_batch1"] = 54.4
    real["hardware"] = "Apple M4 (MPS)"
    real["train_epochs"] = 20
    return JSONResponse(real)


@app.post("/api/predict")
async def predict(file: UploadFile) -> JSONResponse:
    """Real inference on a user-uploaded image. Not precomputed."""
    ext = Path(file.filename or "upload.jpg").suffix or ".jpg"
    uid = uuid.uuid4().hex[:12]
    raw_path = UPLOADS_DIR / f"{uid}_original{ext}"
    annotated_path = UPLOADS_DIR / f"{uid}_annotated.png"

    contents = await file.read()
    raw_path.write_bytes(contents)

    start = time.perf_counter()
    detections = inference.annotate_image(str(raw_path), str(annotated_path))
    elapsed_ms = (time.perf_counter() - start) * 1000

    return JSONResponse(
        {
            "detections": detections,
            "fish_count": len(detections),
            "annotated_url": f"/uploads/{annotated_path.name}",
            "original_url": f"/uploads/{raw_path.name}",
            "inference_ms": round(elapsed_ms, 1),
        }
    )
