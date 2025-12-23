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

