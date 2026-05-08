# main.py — FastAPI backend for Multilingual Video Dubbing

import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pipeline import run_pipeline

app = FastAPI(title="Multilingual Video Dubbing API")

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

LANGUAGES = {
    "English": "en",
    "Telugu": "te",
    "Hindi": "hi",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Arabic": "ar"
}

# Track job status
jobs = {}

def process_job(job_id: str, video_path: str, language_code: str, output_path: str):
    try:
        jobs[job_id] = {"status": "processing", "progress": "Starting pipeline..."}
        run_pipeline(video_path, language_code, output_path)
        jobs[job_id] = {"status": "done", "output": output_path}
    except Exception as e:
        jobs[job_id] = {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

# ================= ROUTES =================

@app.get("/")
def root():
    return {"message": "Dubbing API is running 🎬"}

@app.get("/languages")
def get_languages():
    return LANGUAGES

@app.post("/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    language: str = Form(...)
):
    if language not in LANGUAGES:
        return JSONResponse(status_code=400, content={"error": "Unsupported language"})

    job_id = str(uuid.uuid4())
    ext = os.path.splitext(video.filename)[-1] or ".mp4"
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}_output.mp4")

    # Save uploaded file
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    language_code = LANGUAGES[language]

    # Run pipeline in background
    background_tasks.add_task(process_job, job_id, video_path, language_code, output_path)

    jobs[job_id] = {"status": "queued"}

    return {"job_id": job_id}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return jobs[job_id]

@app.get("/download/{job_id}")
def download_output(job_id: str):
    if job_id not in jobs or jobs[job_id]["status"] != "done":
        return JSONResponse(status_code=404, content={"error": "Output not ready"})

    output_path = jobs[job_id]["output"]
    return FileResponse(output_path, media_type="video/mp4", filename="dubbed_output.mp4")
