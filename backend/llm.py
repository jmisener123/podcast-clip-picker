import json
import os
from groq import Groq

def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    return Groq(api_key=api_key)

def pick_best_clip(clips):
    client = get_client()

    prompt = f"""
You are helping select the best podcast clip.

Each clip below is a candidate excerpt from a longer episode.
Pick the ONE clip that would be most compelling for a listener.

Return ONLY valid JSON in this format:
{{
  "index": number,
  "reason": string
}}

Clips:
{json.dumps(clips, indent=2)}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    return json.loads(content)
