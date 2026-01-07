## Project Overview

A meeting assistant that accepts meeting audio, performs speaker diarization and transcription, and generates meeting and speaker-level summaries.

- The system accepts uploaded audio via a Streamlit UI, sends audio to cloud services for diarization and transcription, and uses an LLM to produce summaries. Results (transcript, speaker segments, summaries) are stored locally and available for download via the UI.

## Architecture Overview

- Main components

	1. Streamlit UI — user-facing interface for uploading audio, specifying parameters, and downloading results.
	2. FastAPI backend — handles API endpoints for processing requests, coordinating uploads, and serving results to the UI.
	3. pyannote Cloud — used for speaker diarization and (cloud) transcription; the backend sends audio to pyannote and receives per-speaker time segments and transcripts.
	4. Ollama Cloud — used as the LLM provider to generate meeting-level and speaker-level summaries from transcripts and speaker-segmented text.


## Models and External Services

- pyannote Cloud

	- Purpose: speaker diarization and transcription (segmenting audio by speaker and producing text for segments).

- Ollama Cloud

	- Purpose: large language model used for summarization of meeting transcripts and speaker-specific content.

- Operational notes

	- Diarization accuracy depends on audio quality (noise, overlap, microphone placement).
	- Providing an accurate `numSpeakers` improves diarization results.

## Features Implemented

- Audio upload via Streamlit UI
- Speaker diarization using pyannote Cloud
- Transcript generation (per-segment and aggregated)
- Meeting-level summarization via LLM
- Speaker-wise summarization via LLM
- Transcript download from the UI
- Streamlit-based UI for interaction and results visualization

## Prerequisites

- Python 3.11 or newer (3.11 recommended).
- `pip` for installing Python dependencies.
- Virtual environment tooling recommended (venv, virtualenv, or pipenv).

## Installation

1. (Optional) Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Environment Variables

The application expects the following environment variables to be set for cloud integration. If some variables appear commented or unused in code, they can be ignored until the corresponding integration is enabled.

- `PYANNOTE_API_KEY` — API key for pyannote Cloud (diarization and transcription).
- `OLLAMA_API_KEY` — API key for Ollama Cloud (LLM summarization).
- `LLM_PROVIDER` — provider label used by the LLM client (e.g., `ollama`).
- `LLM_MODEL` — model identifier to use with the configured LLM provider.



## Running the Application

- Start the FastAPI backend (from project root):

```bash
# Example using uvicorn; adjust module path if different
uvicorn app.api.routes:app --reload --port 8000
```

- Start the Streamlit UI (from project root):

```bash
streamlit run demo_app.py
```

- Open these URLs in your browser:

	- Streamlit UI: http://localhost:8501 
	- Refer api docs: http://localhost:8000/docs

Notes:
- The `--reload` and single-process `uvicorn` invocation are for development only. For production, run multiple workers (e.g., `uvicorn --workers 4`) behind a reverse proxy and set proper host/bind options.
- The backend now enqueues long-running processing as background jobs and exposes a job-status endpoint; the UI polls for job completion instead of blocking the request.

## Usage Flow

1. Open the Streamlit UI.
2. Upload an audio file (supported formats per the capture code).
3. Specify `numSpeakers` (recommended for better diarization) and other parameters.
4. Trigger processing; the UI calls the FastAPI backend which orchestrates cloud calls.
5. After processing, view the meeting-level summary and per-speaker summaries in the UI.
6. Download the full transcript (single file) from the UI.

## Known Limitations

- Long-running processing runs in background jobs; results are persisted and the UI polls job status.
- Diarization quality degrades if `numSpeakers` is incorrect or audio quality is poor.
- No live meeting capture integration is implemented yet.
- No production-grade security, rate-limiting, or robustness features implemented.

Supported formats & limits
- Supported audio formats: WAV, MP3, M4A (recommended: 16kHz mono). Avoid very large files in the UI — if you expect large uploads, use chunking or direct object storage.

Security & privacy 
- Use `ENABLE_REDACTION` to control redaction; redaction currently relies on the LLM and will be hardened before production.


Contribution / PR checklist
- Include a short PR description, list security/privacy impacts, and link any issues for deferred checks. Ensure tests pass locally before requesting review.

## Future Improvements / Roadmap

- Add real-time meeting bot integrations (Google Meet, Microsoft Teams) for live capture.
- Map speaker segments to real names (speaker name mapping and verification UX).
- Add evaluation metrics and automated tests for diarization and summarization quality.
- Security, privacy & LLM checks.

## Disclaimer

- This project is a experimental system. It is not intended for production use without further hardening, security review, and operational validation.

---

