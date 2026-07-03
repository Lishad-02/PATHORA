import json
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# =====================================
# CONFIG (LLM OWNED BY THIS FILE)
# =====================================

GEMINI_API_KEY = "AIzaSyCj0d7ItRTTfHeLXsc69CxDLAv8OwCUbRo"
MODEL_NAME = "models/gemini-2.5-flash"

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "step1_generated_skills.json"

# =====================================
# PROMPT TEMPLATE (FREE REASONING)
# =====================================

PROMPT_TEMPLATE = """
You are a senior technical hiring mentor and software engineer.

Your task is to recommend skills that will make a user job-ready.

User profile:
- Job type: {job_type}
- Target role: {specific_role}
- Experience level: {experience_level}
- Preparation time: {preparation_time} months
- Daily study hours: {study_hours}
- Target location: {location}

Additional preferences:
{other_preferences}

Instructions:
1. Recommend skills required to become job-ready.
2. Include:
   - Core skills
   - Supporting skills
   - Prerequisite or foundational skills
3. Be realistic about what can be achieved within the given time.
4. Do NOT mention job-market statistics or frequencies.
5. Do NOT include learning resources or schedules.

Output STRICT JSON only in this format:

{{
  "skills": [
    {{
      "skill": "Skill name",
      "reason": "Why this skill is important for job readiness"
    }}
  ]
}}

Do not add any explanation outside the JSON.
"""

# =====================================
# HELPER: CLEAN LLM OUTPUT
# =====================================

def clean_llm_output(text: str) -> str:
    """
    Removes Markdown code fences like ```json ... ``` if present.
    """
    text = text.strip()

    if text.startswith("```"):
        # Remove opening fence
        text = text.split("```", 1)[1]

        # Remove optional language tag (json)
        text = text.lstrip()
        if text.startswith("json"):
            text = text[4:]

        # Remove closing fence
        if "```" in text:
            text = text.rsplit("```", 1)[0]

    return text.strip()

# =====================================
# MAIN FUNCTION (CALLED BY main.py)
# =====================================

def generate_skills(user_preferences: dict) -> dict:
    """
    Generates job-ready skill recommendations using Gemini.
    Saves output to JSON file.
    """

    # Configure Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    # Build prompt
    prompt = PROMPT_TEMPLATE.format(
        job_type=user_preferences["job_type"],
        specific_role=user_preferences["specific_role"],
        experience_level=user_preferences["experience_level"],
        preparation_time=user_preferences["preparation_time"],
        study_hours=user_preferences["study_hours"],
        location=user_preferences["location"],
        other_preferences=user_preferences["other_preferences"]
    )

    # LLM call
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Clean Markdown if present
    cleaned_text = clean_llm_output(raw_text)

    # Parse JSON safely
    try:
        parsed_output = json.loads(cleaned_text)
    except json.JSONDecodeError:
        raise ValueError(
            "❌ LLM output is not valid JSON after cleaning:\n\n" + raw_text
        )

    # Save output
    final_output = {
        "generated_at": datetime.utcnow().isoformat(),
        "user_preferences": user_preferences,
        "recommended_skills": parsed_output
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    return final_output
