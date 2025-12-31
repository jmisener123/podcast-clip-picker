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
        print(f"JSON decode error: {e}")
        print(f"Attempted to parse: {content}")
        # Try fixing common issues
        try:
            # Fix 1: Add quotes around unquoted "reason" values (e.g., "reason": * text -> "reason": "* text")
            content_fixed = re.sub(
                r'"reason":\s*(\*[^}]+)',
                lambda m: f'"reason": "{m.group(1).strip()}"',
                content
            )
            
            # Fix 2: Fix unescaped newlines within string values
            def fix_newlines_in_strings(match):
                string_content = match.group(1)
                # Replace literal newlines with spaces
                fixed = string_content.replace('\n', ' ').replace('\r', '')
                return f'"{fixed}"'
            
            # Match quoted strings and fix newlines inside them
            content_fixed = re.sub(r'"([^"]*?)"', fix_newlines_in_strings, content_fixed, flags=re.DOTALL)
            
            print(f"Repaired JSON: {content_fixed}")
            return json.loads(content_fixed)
        except json.JSONDecodeError as e2:
            print(f"Second JSON decode error: {e2}")
            print(f"Final attempted content: {content_fixed if 'content_fixed' in locals() else content}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e2}. Content: {content[:200]}")

def pick_best_clip(clips):
    client = get_client()
    
    # Format clips with clear labeling
    formatted_clips = []
    for i, clip in enumerate(clips):
        clip_info = {
            "index": i,
            "timestamp": f"{clip['start_seconds']//60}:{clip['start_seconds']%60:02d} - {clip['end_seconds']//60}:{clip['end_seconds']%60:02d}",
            "text": clip["text"]
        }
        # Add names if found
        if clip.get("names"):
            clip_info["speakers_mentioned"] = clip["names"]
        formatted_clips.append(clip_info)

    prompt = f"""
You are helping select the best short podcast clip to share publicly.

Each clip below is a candidate excerpt from a longer podcast episode, labeled with an index number.

Your goal is to pick the ONE clip that would be most compelling to a new listener who has never heard this podcast.

A strong clip should have at least ONE of these qualities:
- **Actionable advice or tactics** - Specific steps, methods, or practices someone can immediately apply
- **Surprising insight or counterintuitive idea** - Challenges conventional wisdom or reveals something unexpected
- **Concrete story or example** - Real anecdote with specific details (names, numbers, situations)
- **Controversial or bold statement** - Strong opinion that sparks thought or debate
- **Practical framework or mental model** - A clear way to think about a problem

AVOID clips that are:
- Vague platitudes or generic advice ("be yourself", "work hard", "stay positive")
- Abstract philosophy without concrete examples
- Introductions, outros, ads, or housekeeping
- Dependent on prior context from the episode
- Meandering conversations without a clear point

Prioritization (most to least important):
1. Actionable and specific (HOW to do something, not just WHAT to do)
2. Contains concrete examples, numbers, names, or stories
3. Memorable and quotable
4. Self-contained and immediately understandable

Pick the single best clip based on these criteria.

IMPORTANT: Your "reason" field MUST describe the content of the clip you selected. Read the clip text carefully before writing the reason.

For the "reason" field:
- Use 3-4 concise bullets that summarize the ACTUAL conversation in the SELECTED clip.
- CRITICAL: If a clip has a "speakers_mentioned" field, you MUST use those exact names when referring to the speakers. Never write "the speaker" or "they" - always use the actual person's name from the speakers_mentioned field.
- If no names are in speakers_mentioned, you may use "the speaker" as a fallback.
- Include specific details like roles/titles, concrete examples, numbers, or key quotes from the transcript.
- **Bold important words or phrases** using markdown syntax (e.g., **John Smith**, **CEO**, **$1 million**).
- Format bullets using "* " at the start of each line, separated by spaces (NOT as a JSON array)
- Don't use any intro sentence like "I chose this because" or "This clip is great because".
- Focus on the content of the clip, not your decision process.
- Do NOT use generic descriptions - be specific about what is actually said in the clip.
- Do NOT describe clips you didn't select
- Do NOT say "I chose this because"
- Write in a casual, informal tone as if summarizing to a friend.

Return ONLY valid JSON in this format:
{{
  "index": number,
  "reason": "* First bullet point * Second bullet point * Third bullet point"
}}

Example correct response:
{{
  "index": 2,
  "reason": "* **Sarah** discusses her framework for productivity * She mentions the **80/20 rule** * Gives a specific example of how she eliminated **5 hours** of meetings per week"
}}

CRITICAL FORMATTING RULES:
- The "reason" value MUST be enclosed in double quotes: "reason": "your text here"
- The "reason" MUST be a single-line STRING with NO newlines or line breaks
- Separate bullet points with spaces ONLY (use " * " between bullets)
- Do NOT use \n or actual line breaks in the reason string
- Keep the entire JSON on as few lines as possible

Return ONLY valid JSON in this format:
{{
  "index": number,
  "reason": string
}}

Important:
- The index must match the clip you're describing in the reason
- Do not include newlines, tabs, or control characters inside string values
- All strings must be valid JSON strings
- Do not include text before or after the JSON object

Clips:
{json.dumps(formatted_clips, indent=2)}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    
    
    return parse_json_response(content)
