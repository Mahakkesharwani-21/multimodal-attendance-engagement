import wave
import numpy as np

def analyze_audio(path, frame_ms=100, threshold_multiplier=2.2):
    with wave.open(path, "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)
    if width == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32)-128) / 128
    elif width == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    elif width == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648
    else:
        raise ValueError("Unsupported WAV sample width. Use 8-, 16-, or 32-bit PCM WAV.")
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    if not len(data) or rate <= 0:
        raise ValueError("Audio file is empty or invalid.")
    frame_len = max(1, int(rate * frame_ms / 1000))
    usable = len(data) // frame_len * frame_len
    chunks = data[:usable].reshape(-1, frame_len) if usable else data.reshape(1, -1)
    rms = np.sqrt(np.mean(chunks**2, axis=1) + 1e-12)
    floor = float(np.percentile(rms, 25))
    threshold = max(floor * threshold_multiplier, 0.008)
    active = rms > threshold
    ratio = float(np.mean(active)) if len(active) else 0.0
    # Count transitions into active regions, ignoring single-frame blips.
    active_segments = 0
    in_seg = False
    seg_len = 0
    for val in active:
        if val:
            seg_len += 1
            if not in_seg:
                in_seg = True
        else:
            if in_seg and seg_len >= 2: active_segments += 1
            in_seg = False; seg_len = 0
    if in_seg and seg_len >= 2: active_segments += 1
    return {
        "duration_seconds": len(data) / rate,
        "activity_ratio": ratio,
        "active_segments": active_segments,
        "energy_curve": [round(float(x), 5) for x in rms[::max(1, len(rms)//200)]],
        "threshold": threshold
    }
