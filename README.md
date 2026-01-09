# Podcast Clip Picker

A web app that finds the most shareable clip from any YouTube podcast episode.

Paste a link, optionally filter by topic or clip type, and get a timestamped result with an embedded preview.

## Features

- **Automatic clip selection** - Analyzes the full transcript and picks the best moment
- **Topic search** - Find clips about a specific subject (e.g., "AI", "hiring", "productivity")
- **Clip type filter** - Choose what you're looking for:
  - Actionable advice
  - Surprising insights
  - Concrete stories
  - Controversial takes
  - Funny moments
  - Emotional/inspiring content
- **Embedded preview** - Watch the selected clip directly in the app
- **Context-aware explanations** - See who's speaking and why the clip matters

## How It Works

1. Fetches the YouTube transcript
2. Generates candidate clips throughout the episode (skipping intros)
3. Filters by topic if specified
4. Uses an LLM to evaluate and select the best clip based on your criteria
5. Returns the timestamp with an explanation

## Tech Stack

**Backend**: Python, FastAPI, Groq (Llama 3.3), youtube-transcript-api

**Frontend**: React, Vite

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn youtube-transcript-api groq python-dotenv requests
```

Create `backend/.env`:
```
GROQ_API_KEY=your_api_key_here
```

Run:
```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## API

**POST /pick-clip**

```json
{
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "criteria": ["funny"],
  "topic": "AI"
}
```

Response:
```json
{
  "start_seconds": 342,
  "end_seconds": 401,
  "reason": "- **Sam Altman** explains why...",
  "title": "Episode Title",
  "channel_name": "Channel Name"
}
```

Both `criteria` and `topic` are optional.
