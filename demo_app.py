import streamlit as st
import requests
import tempfile
import os
import time

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
FASTAPI_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Meeting Assistant",
    layout="wide",
)

st.title("🧠 Meeting Assistant")
st.write(
    "Upload a meeting audio file, specify number of speakers, "
    "and get a structured meeting summary with speaker-wise insights."
)

# --------------------------------------------------
# SIDEBAR INPUTS
# --------------------------------------------------
st.sidebar.header("Input Parameters")

num_speakers = st.sidebar.number_input(
    "Number of Speakers",
    min_value=1,
    max_value=20,
    value=2,
    step=1,
)

uploaded_file = st.file_uploader(
    "Upload Meeting Audio",
    type=["wav", "mp3", "m4a"],
)

process_btn = st.button("🚀 Process Meeting")

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "meeting_summary" not in st.session_state:
    st.session_state.meeting_summary = None

if "speaker_summaries" not in st.session_state:
    st.session_state.speaker_summaries = None

if "transcript" not in st.session_state:
    st.session_state.transcript = None

# --------------------------------------------------
# MAIN PROCESS FLOW
# --------------------------------------------------
if process_btn:
    if not uploaded_file:
        st.warning("Please upload an audio file.")
        st.stop()

    # -------------------------------
    # Upload audio to FastAPI
    # -------------------------------
    with st.spinner("Uploading audio file..."):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=uploaded_file.name
        ) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            upload_response = requests.post(
                f"{FASTAPI_BASE_URL}/upload-audio",
                files={"file": f},
            )

        os.unlink(tmp_path)

        if upload_response.status_code != 200:
            st.error("Failed to upload audio file.")
            st.stop()

        audio_url = upload_response.json()["audio_url"]

    # -------------------------------
    # Run diarization + summarization (enqueue + poll)
    # -------------------------------
    with st.spinner("Submitting job..."):
        process_response = requests.post(
            f"{FASTAPI_BASE_URL}/process-audio",
            params={"audio_url": audio_url, "num_speakers": num_speakers},
        )

        if process_response.status_code != 200:
            st.error("Processing request failed.")
            st.stop()

        job_id = process_response.json().get("job_id")

    # poll for result
    with st.spinner("Processing in background (this may take several minutes)..."):
        poll_interval = 2  # seconds
        max_wait = 60 * 10  # 10 minutes
        waited = 0

        while waited < max_wait:
            status_resp = requests.get(f"{FASTAPI_BASE_URL}/jobs/{job_id}")
            if status_resp.status_code != 200:
                st.error("Failed to fetch job status.")
                st.stop()

            status_data = status_resp.json()
            status = status_data.get("status")
            if status == "done":
                result = status_data.get("result", {})
                st.session_state.meeting_summary = result.get("meeting_summary")
                st.session_state.speaker_summaries = result.get("speakers")
                st.session_state.transcript = result.get("transcript")
                break
            if status == "failed":
                st.error(f"Processing failed: {status_data.get('error')}")
                break

            time.sleep(poll_interval)
            waited += poll_interval
        else:
            st.warning(
                "Processing is still running; try again later and refresh this page."
            )

# --------------------------------------------------
# OUTPUT: MEETING SUMMARY
# --------------------------------------------------
if st.session_state.meeting_summary:
    st.subheader("📌 Meeting Summary")
    st.success(st.session_state.meeting_summary)

# --------------------------------------------------
# OUTPUT: SPEAKER SUMMARIES
# --------------------------------------------------
if st.session_state.speaker_summaries:
    st.subheader("🗣️ Speaker-wise Summaries")

    for speaker_id, summary in st.session_state.speaker_summaries.items():
        with st.expander(speaker_id):
            st.write(summary)

# --------------------------------------------------
# OUTPUT: TRANSCRIPT DOWNLOAD
# --------------------------------------------------
if st.session_state.transcript:
    st.subheader("⬇️ Download Transcript")

    st.download_button(
        label="Download Transcript (.txt)",
        data=st.session_state.transcript,
        file_name="meeting_transcript.txt",
        mime="text/plain",
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption("Powered by FastAPI · pyannote Cloud · Ollama")
