import streamlit as st
import cv2
import numpy as np
import pandas as pd
import sqlite3
import tempfile
import os
from datetime import datetime
from pathlib import Path

from modules.database import init_db, save_attendance, load_attendance, save_session, load_sessions
from modules.vision import analyze_video
from modules.audio import analyze_audio
from modules.analytics import make_suggestions, combine_engagement

st.set_page_config(page_title="Multimodal Attendance & Engagement Agent", page_icon="🎓", layout="wide")
init_db()

st.title("🎓 Multimodal Attendance & Engagement Agent")
st.caption("Local-first classroom analytics prototype • Video and audio are processed on this device.")

with st.sidebar:
    st.header("Session settings")
    session_name = st.text_input("Session / class name", value="Classroom Session")
    min_presence = st.slider("Minimum sustained presence (seconds)", 1, 30, 5)
    sample_every = st.slider("Analyze every Nth video frame", 1, 60, 10)
    st.divider()
    st.caption("Privacy: use consented recordings. This prototype does not identify people by name or infer emotions.")

tab1, tab2, tab3, tab4 = st.tabs(["📹 Video & Attendance", "🎙️ Audio Analysis", "📊 Analytics", "🗂️ Session History"])

with tab1:
    st.subheader("Automated attendance tracking")
    st.write("Upload a classroom video. Face detection is performed locally. Sustained detections are grouped into anonymous participant tracks; they are not biometric identity verification.")
    video_file = st.file_uploader("Upload video", type=["mp4", "mov", "avi", "mkv"], key="video")
    if video_file:
        st.video(video_file)
        if st.button("Analyze video", type="primary"):
            suffix = Path(video_file.name).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_file.getbuffer())
                video_path = tmp.name
            try:
                with st.spinner("Analyzing video locally..."):
                    result = analyze_video(video_path, min_presence=min_presence, sample_every=sample_every)
                st.session_state["vision_result"] = result
                st.session_state["active_session_name"] = session_name
                st.success("Video analysis complete.")
            except Exception as exc:
                st.error(f"Could not analyze this video: {exc}")
            finally:
                try: os.remove(video_path)
                except OSError: pass

    result = st.session_state.get("vision_result")
    if result:
        c1, c2, c3 = st.columns(3)
        c1.metric("Anonymous tracks", result["participant_count"])
        c2.metric("Frames sampled", result["frames_sampled"])
        c3.metric("Video duration", f'{result["duration_seconds"]:.1f} sec')
        st.info("Tracks are anonymous visual tracks, not verified student identities. Review results before using for official attendance.")
        df = pd.DataFrame(result["attendance"])
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download attendance CSV", csv, "attendance.csv", "text/csv")
            if st.button("Save attendance and session locally"):
                sid = save_session(st.session_state.get("active_session_name", session_name),
                                   result["duration_seconds"], result["participant_count"],
                                   result.get("mean_presence_ratio", 0.0), "video")
                for row in result["attendance"]:
                    save_attendance(sid, row)
                st.success(f"Saved session #{sid} to local SQLite database.")
        if result.get("preview_jpeg"):
            st.image(result["preview_jpeg"], caption="Last analyzed frame (faces blurred for preview)", use_container_width=True)

with tab2:
    st.subheader("Audio activity and interaction analysis")
    st.write("Upload a WAV recording. The tool estimates speech-like activity from short-time audio energy; it does not transcribe speech or identify speakers.")
    audio_file = st.file_uploader("Upload WAV audio", type=["wav"], key="audio")
    if audio_file:
        st.audio(audio_file)
        if st.button("Analyze audio", type="primary"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_file.getbuffer())
                audio_path = tmp.name
            try:
                with st.spinner("Analyzing audio locally..."):
                    audio_result = analyze_audio(audio_path)
                st.session_state["audio_result"] = audio_result
                st.success("Audio analysis complete.")
            except Exception as exc:
                st.error(f"Could not analyze audio: {exc}")
            finally:
                try: os.remove(audio_path)
                except OSError: pass
    ar = st.session_state.get("audio_result")
    if ar:
        c1, c2, c3 = st.columns(3)
        c1.metric("Duration", f'{ar["duration_seconds"]:.1f} sec')
        c2.metric("Activity ratio", f'{ar["activity_ratio"]*100:.1f}%')
        c3.metric("Activity segments", ar["active_segments"])
        st.line_chart(pd.DataFrame({"Audio energy": ar["energy_curve"]}))
        st.caption("Audio activity is a rough signal-level estimate. Background noise can affect results.")

with tab3:
    st.subheader("Engagement insights and teaching suggestions")
    vr = st.session_state.get("vision_result")
    ar = st.session_state.get("audio_result")
    if vr:
        audio_ratio = ar["activity_ratio"] if ar else None
        metrics = combine_engagement(vr, audio_ratio)
        cols = st.columns(3)
        cols[0].metric("Movement activity", f'{metrics["movement_activity"]*100:.1f}%')
        cols[1].metric("Inactivity indicator", f'{metrics["inactivity_indicator"]*100:.1f}%')
        cols[2].metric("Audio activity", f'{audio_ratio*100:.1f}%' if audio_ratio is not None else "Not analyzed")
        st.write("These are observable session-level indicators, not a measure of a student's internal attention or emotions.")
        for suggestion in make_suggestions(metrics, audio_ratio):
            st.markdown(f"- {suggestion}")
        st.download_button("Download analytics JSON",
                           pd.Series({**metrics, "suggestions": make_suggestions(metrics, audio_ratio)}).to_json(indent=2),
                           "session_analytics.json", "application/json")
    else:
        st.info("Analyze a video first to generate session analytics. Audio analysis is optional.")

with tab4:
    st.subheader("Locally stored session history")
    sessions = load_sessions()
    if sessions:
        sdf = pd.DataFrame(sessions)
        st.dataframe(sdf, use_container_width=True)
        sid = st.selectbox("Choose session ID to view attendance", sdf["id"].tolist())
        adf = pd.DataFrame(load_attendance(int(sid)))
        if not adf.empty:
            st.dataframe(adf, use_container_width=True)
            st.download_button("Export saved attendance CSV", adf.to_csv(index=False).encode("utf-8"),
                               f"attendance_session_{sid}.csv", "text/csv")
    else:
        st.info("No saved sessions yet. Analyze a video and choose “Save attendance and session locally.”")

st.divider()
st.caption("Educational prototype. Do not use as the sole basis for grading, discipline, or official attendance decisions.")
