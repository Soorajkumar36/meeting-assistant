import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
import json
import asyncio
from typing import Dict, Any
from fastapi import BackgroundTasks

from app.storage.upload_store import UploadStore
from app.main import run_pipeline_with_audio_url
from app.config import load_config


app = FastAPI(
    title="Meeting Assistant API",
    version="0.1.0",
)

# --------------------------------------------------
# Static file hosting for pyannote
# --------------------------------------------------
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
config = load_config()

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads",
)

upload_store = UploadStore(base_dir=str(UPLOAD_DIR))


# --------------------------------------------------
# Job storage for background processing
# --------------------------------------------------
JOB_DIR = Path("data/summaries/jobs")
JOB_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job status (kept for quick lookup). Persistent results are stored
# as JSON files under `JOB_DIR` so they survive process restarts.
job_status: Dict[str, Dict[str, Any]] = {}


async def _process_job(job_id: str, audio_url: str, num_speakers: int):
    job_status[job_id] = {"status": "running"}
    try:
        meeting_summary, speaker_summaries, transcript_text = await asyncio.to_thread(
            run_pipeline_with_audio_url,
            audio_url,
            num_speakers,
        )

        result = {
            "meeting_summary": meeting_summary.overview,
            "speakers": {s.speaker_id: s.summary for s in speaker_summaries},
            "transcript": transcript_text,
        }

        out_path = JOB_DIR / f"{job_id}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

        job_status[job_id].update({"status": "done", "result_path": str(out_path)})
    except Exception as exc:  # persist error for inspection
        job_status[job_id].update({"status": "failed", "error": str(exc)})


# --------------------------------------------------
# Health check
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# Upload audio
# --------------------------------------------------
@app.post("/upload-audio")
def upload_audio(file: UploadFile = File(...)):
    # Save file locally first
    saved_path = upload_store.save(file)
    
    # Generate unique object key for Pyannote storage
    object_key = saved_path.stem  # e.g., "1735404531.458927"
    
    # Get API key from config
    api_key = config.asr.pyannote_api_key  # ← Use config
    if not api_key:
        raise HTTPException(status_code=500, detail="PYANNOTE_API_KEY not configured")
    
    try:
        # Step 1: Create pre-signed PUT URL
        response = requests.post(
            "https://api.pyannote.ai/v1/media/input",
            json={"url": f"media://{object_key}"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        presigned_url = response.json()["url"]
        
        # Step 2: Upload file to Pyannote storage
        with open(saved_path, "rb") as audio_file:
            upload_response = requests.put(presigned_url, data=audio_file)
            upload_response.raise_for_status()
        
        # Return the media:// URL that can be used for processing
        pyannote_url = f"media://{object_key}"
        
        return {
            "status": "uploaded",
            "audio_url": pyannote_url,
            "object_key": object_key,
            "local_path": str(saved_path)
        }
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload to Pyannote: {str(e)}"
        )

# --------------------------------------------------
# Run pipeline
# --------------------------------------------------
@app.post("/process-audio")
async def process_audio(audio_url: str, num_speakers: int = 2, background_tasks: BackgroundTasks = None):
    """Enqueue processing and return a job id immediately.

    The heavy work runs in a thread via `asyncio.to_thread` inside the
    background task so the FastAPI event loop isn't blocked.
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = {"status": "queued"}

    # schedule background work
    background_tasks.add_task(_process_job, job_id, audio_url, num_speakers)

    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    info = job_status.get(job_id)
    if not info:
        # Maybe there's a persisted result file; check disk
        candidate = JOB_DIR / f"{job_id}.json"
        if candidate.exists():
            result = json.loads(candidate.read_text(encoding="utf-8"))
            return {"job_id": job_id, "status": "done", "result": result}
        raise HTTPException(status_code=404, detail="job not found")

    if info.get("status") == "done" and info.get("result_path"):
        result = json.loads(Path(info["result_path"]).read_text(encoding="utf-8"))
        return {"job_id": job_id, "status": "done", "result": result}

    return {"job_id": job_id, "status": info.get("status"), "error": info.get("error")}