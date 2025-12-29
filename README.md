# 🎧 Podcast Clip Picker

A full-stack web app that analyzes a podcast episode and selects the **single most compelling short clip** for sharing.

The app:
- pulls a YouTube transcript
- evaluates candidate clip excerpts
- uses an LLM to choose the best clip
- returns a timestamped result that can be embedded or shared

Built as a learning project to explore **FastAPI, React, LLMs, and modern full-stack workflows**.

---

## ✨ What It Does

1. User submits a YouTube link to a podcast episode
2. Backend fetches the transcript
3. Transcript is split into candidate clips
4. An LLM selects the *one* clip most likely to hook a new listener
5. The app returns:
   - the chosen clip index
   - a short explanation of why it works
   - the timestamp for embedding the video

---

## 🧠 Why This Exists

Finding good podcast clips is usually manual and time-consuming.

This project explores whether an LLM can:
- recognize self-contained moments
- identify hooks and insights
- avoid intros, ads, and filler
- make editorial-style judgments

---

## 🛠️ Tech Stack

**Backend**
- Python
- FastAPI
- youtube-transcript-api
- YouTube oEmbed API for title and channel name
- Groq LLM API (Llama)
- python-dotenv

**Frontend**
- React (Vite)
- Fetch API

**Other**
- Git + GitHub
- Environment-based config (`.env`)
- JSON-based LLM contracts