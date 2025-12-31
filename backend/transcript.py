from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import requests
import re

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

def get_video_metadata(video_id: str):
    """Get video title and channel name from YouTube."""
    try:
        # Use YouTube oEmbed API (no API key required)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", ""),
                "channel_name": data.get("author_name", "")
            }
    except Exception as e:
        print(f"Error fetching video metadata: {e}")
    
    return {
        "title": "",
        "channel_name": ""
    }

def generate_candidate_clips(snippets, target_duration=60, max_candidates=10):
    """Generate candidate clips from transcript snippets, sampling throughout the podcast."""
    if not snippets:
        raise ValueError("No snippets provided")
    
    # Calculate total duration
    total_duration = snippets[-1]["end"] - snippets[0]["start"]
    
    # Skip the first 60 seconds to avoid intros
    skip_duration = 60
    
    # Calculate interval to sample clips evenly throughout the podcast
    usable_duration = total_duration - skip_duration
    interval = usable_duration / (max_candidates + 1)
    
    candidates = []
    
    for i in range(max_candidates):
        # Calculate target start time for this candidate
        target_start_time = skip_duration + (i + 1) * interval
        
        # Find the snippet closest to this target time
        start_idx = 0
        for idx, s in enumerate(snippets):
            if s["start"] >= target_start_time:
                start_idx = idx
                break
        
        # Build a clip starting from this position
        current_clip = []
        current_total = 0
        
        for snippet_idx in range(start_idx, len(snippets)):
            s = snippets[snippet_idx]
            text = s["text"].strip()
            
            # Skip non-speech snippets
            if not text or text.startswith("[") or "♪" in text:
                continue
            
            current_clip.append(s)
            current_total += s["end"] - s["start"]
            
            # Keep going until we hit the target duration
            if current_total >= target_duration:
                break
        
        # Only add if we have a valid clip that meets minimum duration
        if current_clip and current_total >= 45:  # At least 45 seconds
            clip_text = " ".join([item["text"].strip() for item in current_clip])
            candidates.append({
                "start_seconds": int(current_clip[0]["start"]),
                "end_seconds": int(current_clip[-1]["end"]),
                "text": clip_text
            })
    
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


def extract_names_from_text(text):
    """Extract potential speaker names from transcript text using LLM."""
    from llm import get_client
    import json
    
    client = get_client()
    
    prompt = f"""Extract the names of any people mentioned or speaking in this podcast transcript excerpt.

Return ONLY a JSON object with a "names" array containing the full names of people (first and last name if available).

Rules:
- Only include actual person names that are explicitly mentioned or who introduce themselves
- Include the speaker's name if they say "I'm [Name]", "My name is [Name]", etc.
- Do NOT include: brand names, company names, or generic references like "the host"
- Return an empty array if no names are found

Transcript excerpt:
{text[:1000]}

Return format: {{"names": ["Name One", "Name Two"]}}
"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        
        content = response.choices[0].message.content.strip()
        # Try to extract JSON
        if '```' in content:
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
        
        result = json.loads(content)
        return result.get("names", [])
    except Exception as e:
        print(f"Error extracting names with LLM: {e}")
        return []
