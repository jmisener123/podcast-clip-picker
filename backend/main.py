from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from transcript import extract_video_id, get_transcript, generate_candidate_clips, get_video_metadata, extract_names_from_text
from llm import pick_best_clip
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClipRequest(BaseModel):
    youtube_url: str

class ClipResponse(BaseModel):
    start_seconds: int
    end_seconds: int
    reason: str
    title: str
    channel_name: str

@app.post("/pick-clip", response_model=ClipResponse)
def pick_clip(payload: ClipRequest):
    video_id = extract_video_id(payload.youtube_url)
    transcript = get_transcript(video_id)
    
    # Get video metadata
    metadata = get_video_metadata(video_id)
    
    # Normalize snippets: convert duration to end time
    snippets = []
    for item in transcript:
        snippets.append({
            "text": item.text,
            "start": item.start,
            "end": item.start + item.duration
        })
    
    # Generate candidate clips
    candidates = generate_candidate_clips(snippets)
    
    # Extract names from each candidate clip
    for candidate in candidates:
        candidate["names"] = extract_names_from_text(candidate["text"])
    
    # Use LLM to pick the best clip
    choice = pick_best_clip(candidates)
    
    best_clip = candidates[choice["index"]]
    best_clip["reason"] = choice["reason"]
    best_clip["title"] = metadata["title"]
    best_clip["channel_name"] = metadata["channel_name"]
    
    return best_clip
