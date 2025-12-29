from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def extract_video_id(youtube_url: str) -> str:
    parsed = urlparse(youtube_url)

    if "youtube.com" in parsed.netloc:
        return parse_qs(parsed.query)["v"][0]

    if "youtu.be" in parsed.netloc:
        return parsed.path.lstrip("/")

    raise ValueError("Invalid YouTube URL")

def get_transcript(video_id: str):
    api = YouTubeTranscriptApi()
    return api.fetch(video_id, languages=["en-US", "en"])

def generate_candidate_clips(snippets, target_duration=40, max_candidates=3):
    """Generate candidate clips from transcript snippets."""
    candidates = []
    current_clip = []
    current_total = 0
    snippet_idx = 0

    while snippet_idx < len(snippets) and len(candidates) < max_candidates:
        s = snippets[snippet_idx]
        text = s["text"].strip()

        if not text or text.startswith("[") or "♪" in text:
            snippet_idx += 1
            continue

        current_clip.append(s)
        current_total += s["end"] - s["start"]

        if current_total >= target_duration:
            # Create a candidate clip
            clip_text = " ".join([item["text"].strip() for item in current_clip])
            candidates.append({
                "start_seconds": int(current_clip[0]["start"]),
                "end_seconds": int(current_clip[-1]["end"]),
                "text": clip_text
            })
            # Reset for next candidate
            current_clip = []
            current_total = 0

        snippet_idx += 1

    if not candidates:
        raise ValueError("No valid clips found in transcript")

    return candidates

def pick_first_clip(snippets, target_duration=40):
    clip = []
    total = 0

    for s in snippets:
        text = s["text"].strip()

        if not text or text.startswith("[") or "♪" in text:
            continue

        clip.append(s)
        total += s["end"] - s["start"]

        if total >= target_duration:
            break

    if not clip:
        raise ValueError("No valid clips found in transcript")

    return {
        "start_seconds": int(clip[0]["start"]),
        "end_seconds": int(clip[-1]["end"]),
        "reason": "First continuous spoken segment (~40s)"
    }

