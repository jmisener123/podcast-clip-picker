import json
import os
import re
from groq import Groq

def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    return Groq(api_key=api_key)

def parse_json_response(content):
    """Parse JSON from LLM response, handling markdown code blocks and control characters."""
    # Strip whitespace
    original_content = content.strip()
    
    # Helper function to clean control characters
    def clean_control_chars(text):
        """Remove control characters, replacing them with space to preserve structure."""
        result = []
        for char in text:
            code = ord(char)
            # Keep printable ASCII (32-126), newline (10), carriage return (13), tab (9)
            if code >= 32 or code in [9, 10, 13]:
                result.append(char)
            else:
                # Replace control chars with space to avoid breaking JSON structure
                result.append(' ')
        return ''.join(result)
    
    # Try to extract JSON from markdown code blocks FIRST (```json ... ``` or ``` ... ```)
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', original_content, re.DOTALL)
    if json_match:
        content = json_match.group(1)
    else:
        content = original_content
    
    # If no code block, try to find JSON object directly
    if not content.startswith('{'):
        # Find the first { and last } to extract JSON
        start_idx = content.find('{')
        if start_idx != -1:
            # Count braces to find matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            if end_idx > start_idx:
                content = content[start_idx:end_idx]
    
    # Save extracted content before cleaning for fallback
    extracted_content = content
    
    # Clean newlines and control characters in JSON strings FIRST (before general cleaning)
    def clean_json_strings(text):
        """Clean control characters and escape newlines inside JSON string values."""
        result = []
        in_string = False
        escape_next = False
        i = 0
        while i < len(text):
            char = text[i]
            if escape_next:
                result.append(char)
                escape_next = False
            elif char == '\\' and in_string:
                result.append(char)
                escape_next = True
            elif char == '"' and not escape_next:
                result.append(char)
                in_string = not in_string
            elif in_string:
                # Inside a string - handle control chars and newlines
                if char == '\n':
                    # Replace newlines with space (or escape them, but space is simpler)
                    result.append(' ')
                elif char == '\r':
                    # Remove carriage returns
                    continue
                elif char == '\t':
                    # Replace tabs with space
                    result.append(' ')
                else:
                    code = ord(char)
                    if code >= 32:  # Printable ASCII
                        result.append(char)
                    else:
                        result.append(' ')  # Replace other control chars with space
            else:
                # Outside a string - keep as is (preserve structure)
                result.append(char)
            i += 1
        return ''.join(result)
    
    # Clean string values first
    content = clean_json_strings(extracted_content)
    
    # Clean control characters from the extracted JSON (for any remaining issues)
    content = clean_control_chars(content)
    content = content.strip()
    
    # Parse JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Last resort: try with a minimal fix - just remove any remaining problematic chars
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t{}[]":,')
        return json.loads(content)

def pick_best_clip(clips):
    client = get_client()

    prompt = f"""
You are helping select the best short podcast clip to share publicly.

Each clip below is a candidate excerpt from a longer podcast episode.

Your goal is to pick the ONE clip that would be most compelling to a new listener who has never heard this podcast.

A strong clip:
- Is self-contained and understandable on its own
- Contains a clear idea, insight, or emotional moment
- Does NOT rely on context from earlier in the episode
- Avoids ads, intros, outros, or housekeeping. It's usually NOT within the first 30 seconds.
- Feels interesting within the first few seconds

Pick the single best clip. Before selecting, briefly consider:
- Hook strength
- Clarity without context
- Emotional or intellectual impact

Then choose the best clip.

For the "reason" field:
- Use 3-4 concise bullets that summarize the conversation in the clip.
- Don't use any intro sentence like "I chose this because" or "This clip is great because" or "This clip is great because it's self-contained and understandable on its own".
- Focus on the content of the clip, not your decision process. Quote from the transcript to support your choice.
- Do NOT mention other clips
- Do NOT say "I chose this because"

Return ONLY valid JSON in this format:
{{
  "index": number,
  "reason": string
}}

Important:
- Do not include newlines, tabs, or control characters inside string values
- All strings must be valid JSON strings
- Do not include text before or after the JSON object
Clips:
{json.dumps(clips, indent=2)}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    
    # Debug: print first 500 chars to see what we're dealing with
    print("DEBUG: Raw LLM response (first 500 chars):")
    print(repr(content[:500]))
    
    return parse_json_response(content)
