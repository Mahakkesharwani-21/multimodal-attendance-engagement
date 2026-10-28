def combine_engagement(vision_result, audio_ratio=None):
    movement = float(vision_result.get("movement_activity", 0.0))
    movement = max(0.0, min(1.0, movement * 3.0))
    attendance = float(vision_result.get("mean_presence_ratio", 0.0))
    # Inactivity indicator is a proxy from low frame-to-frame visual change, not attention.
    inactivity = max(0.0, min(1.0, 1.0 - movement))
    return {
        "movement_activity": round(movement, 4),
        "inactivity_indicator": round(inactivity, 4),
        "mean_presence_ratio": round(attendance, 4),
        "audio_activity_ratio": round(float(audio_ratio), 4) if audio_ratio is not None else None
    }

def make_suggestions(metrics, audio_ratio=None):
    suggestions = []
    movement = metrics.get("movement_activity", 0)
    inactivity = metrics.get("inactivity_indicator", 0)
    if metrics.get("mean_presence_ratio", 0) < 0.5:
        suggestions.append("Review camera placement and lighting; some participants may be outside the camera view.")
    if inactivity > 0.8:
        suggestions.append("Consider a short question, poll, or pair discussion to vary the session format. Low visual change does not necessarily mean low attention.")
    elif movement > 0.55:
        suggestions.append("Check whether movement reflects a practical activity or camera disturbance before changing the lesson plan.")
    if audio_ratio is not None and audio_ratio < 0.05:
        suggestions.append("If participation is expected, consider a low-pressure discussion prompt; quiet listening may also be appropriate.")
    elif audio_ratio is not None and audio_ratio > 0.65:
        suggestions.append("Review audio segments to distinguish useful discussion from background noise; consider structured turn-taking if needed.")
    if not suggestions:
        suggestions.append("Review these session-level indicators alongside instructor observations and learner feedback before deciding on changes.")
    suggestions.append("Treat all automated insights as decision support; do not infer emotions, intelligence, or individual attention from video/audio alone.")
    return suggestions
