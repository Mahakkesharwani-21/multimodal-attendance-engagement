import cv2
import numpy as np

def analyze_video(video_path, min_presence=5, sample_every=10):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Video file could not be opened. Try an MP4 encoded with H.264.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 else 0.0
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        cap.release()
        raise RuntimeError("OpenCV face detector could not be loaded.")

    # Lightweight centroid association for an educational prototype.
    tracks = {}
    next_id = 1
    sampled = 0
    prev_gray = None
    motion_values = []
    last_frame = None
    frame_idx = 0
    sample_every = max(1, int(sample_every))
    while True:
        ok, frame = cap.read()
        if not ok: break
        if frame_idx % sample_every == 0:
            sampled += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(35, 35))
            now = frame_idx / fps if fps else 0.0
            centers = [(x+w/2, y+h/2, (x,y,w,h)) for (x,y,w,h) in faces]
            # Match each detected face to the nearest recent track.
            used = set()
            for cx, cy, rect in centers:
                best, best_d = None, 1e9
                for tid, t in tracks.items():
                    if tid in used: continue
                    dx, dy = cx-t["cx"], cy-t["cy"]
                    d = (dx*dx+dy*dy)**0.5
                    if d < best_d and d < max(frame.shape[:2]) * 0.18 and now-t["last"] <= max(2.0, sample_every/fps*3):
                        best, best_d = tid, d
                if best is None:
                    best = next_id; next_id += 1
                    tracks[best] = {"cx":cx, "cy":cy, "first":now, "last":now, "hits":0, "rect":rect}
                t = tracks[best]
                t.update({"cx":cx, "cy":cy, "last":now, "hits":t["hits"]+1, "rect":rect})
                used.add(best)
            if prev_gray is not None:
                small1 = cv2.resize(prev_gray, (160, 90))
                small2 = cv2.resize(gray, (160, 90))
                motion_values.append(float(np.mean(cv2.absdiff(small1, small2))/255.0))
            prev_gray = gray
            last_frame = frame.copy()
        frame_idx += 1
    cap.release()

    attendance = []
    threshold_hits = max(2, int(min_presence * fps / sample_every))
    for tid, t in tracks.items():
        observed = max(0.0, t["last"] - t["first"] + sample_every/fps)
        status = "Present (review)" if t["hits"] >= threshold_hits or observed >= min_presence else "Needs review"
        attendance.append({
            "participant": f"Participant {tid}",
            "first_seen_seconds": round(t["first"], 2),
            "last_seen_seconds": round(t["last"], 2),
            "observed_seconds": round(observed, 2),
            "detections": int(t["hits"]),
            "status": status
        })
    # Blur detected faces in preview before displaying.
    preview = None
    if last_frame is not None:
        gray = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.1, 5, minSize=(35,35))
        for (x,y,w,h) in faces:
            roi = last_frame[y:y+h, x:x+w]
            if roi.size:
                last_frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (31,31), 0)
        ok, encoded = cv2.imencode(".jpg", last_frame)
        if ok: preview = encoded.tobytes()
    count = len(tracks)
    return {
        "participant_count": count,
        "frames_sampled": sampled,
        "duration_seconds": float(duration),
        "attendance": attendance,
        "mean_presence_ratio": float(np.mean([min(1, x["observed_seconds"]/max(duration,1)) for x in attendance])) if attendance else 0.0,
        "movement_activity": float(np.mean(motion_values)) if motion_values else 0.0,
        "preview_jpeg": preview
    }
