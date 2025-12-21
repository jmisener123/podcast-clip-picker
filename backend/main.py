from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


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

@app.post("/pick-clip", response_model=ClipResponse)
def pick_clip(payload: ClipRequest):
    return {
        "start_seconds": 300,
        "end_seconds": 420,
        "reason": "Most replayed insight section"
    }
