# Multimodal Attendance & Engagement Agent

A local-first educational prototype for classroom session analysis. It combines:
- Video face detection and lightweight centroid tracking for anonymous attendance candidates
- Sustained-presence heuristic and timestamped attendance logs
- WAV audio-energy analysis for approximate activity periods
- Session-level visual movement/inactivity indicators
- Rule-based teaching suggestions
- Streamlit dashboard and local SQLite history
- CSV and JSON exports

## Important scope and limitations
This is a **working prototype**, not a validated biometric attendance product. Face detection does not identify a person by name. Anonymous tracks can split or merge when people move, occlude one another, or leave the frame. Review the output before treating it as attendance. For actual named attendance, add a consent-based enrollment and identity-verification module after a privacy/security review.

Audio energy is not speech recognition: fans, traffic, and other noise can trigger activity. The engagement indicators are session-level proxies, not a measurement of attention, emotion, or learning. The application does not infer emotion or identify speakers.

## Requirements
- Python 3.10 or newer (Python 3.11 recommended)
- Windows 10/11, macOS, or Ubuntu Linux
- 8 GB RAM minimum; 16 GB recommended
- Camera/video recordings and WAV audio as inputs
- Internet only for initial package installation; analysis runs locally

## Setup (Windows)
1. Install Python 3.11 from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Extract this ZIP.
3. Open the extracted folder in VS Code.
4. Open a terminal in the project folder and run:

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Setup (macOS/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The browser opens a local dashboard, usually at `http://localhost:8501`.

## How to use
1. Open **Video & Attendance**, upload an MP4/MOV/AVI/MKV video, and select **Analyze video**.
2. Adjust minimum sustained presence and frame sampling in the sidebar if needed.
3. Review anonymous participant tracks and download the attendance CSV.
4. Optional: upload a PCM WAV file in **Audio Analysis**.
5. Open **Analytics** for session-level indicators and teaching suggestions.
6. Select **Save attendance and session locally** to store records in `data/attendance.db`.
7. Open **Session History** to review or export saved attendance.

## Suggested project workflow / EPIC mapping
1. Requirements and environment setup — this README, dependencies, privacy notes.
2. Vision module — `modules/vision.py`.
3. Audio module — `modules/audio.py`.
4. AI/rule-based suggestion engine — `modules/analytics.py`.
5. Dashboard, testing, and deployment — `app.py`, `modules/database.py`.

## Testing checklist
- [ ] Test a short video with one visible face.
- [ ] Test a video with multiple visible faces.
- [ ] Test low light and temporary occlusion; document limitations.
- [ ] Test a quiet WAV and a WAV with speech.
- [ ] Confirm CSV and JSON downloads.
- [ ] Confirm session persistence after restarting Streamlit.
- [ ] Test with consented media and delete raw recordings after use.

## Privacy
Process only recordings for which you have permission. Keep recordings on the local device, restrict access to the project folder, and delete temporary/source media when no longer needed. The app stores session summaries and attendance rows in SQLite; it does not store uploaded video/audio files.
