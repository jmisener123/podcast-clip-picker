from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ClipRequest(BaseModel):
    youtube_url: str

@app.post("/pick-clip")
def pick_clip(req: ClipRequest):
    return {
        "start": 0,
        "end": 60,
        "why": "This is a placeholder response."
    }
