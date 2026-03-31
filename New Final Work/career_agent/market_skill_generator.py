import json
import csv
from pathlib import Path
from datetime import datetime
import google.generativeai as genai

# =====================================
# CONFIG
# =====================================

GEMINI_API_KEY = "AIzaSyAsLsqImXZ4RIFhT5CGKybvEPLCDKYOwtQ"
MODEL_NAME = "models/gemini-2.5-flash"

DATA_DIR = Path("data")
OUTPUT_FILE = Path("outputs/stepB_market_skills.json")

# =====================================
# INIT LLM
# =====================================

genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel(MODEL_NAME)

# =====================================
# LOAD CORPUS (JSON)
# =====================================

def load_json_corpus(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

# =====================================
# LOAD CSV CORPUS (if needed)
# =====================================

def load_csv_corpus(filename):
    skills = {}
    with open(DATA_DIR / filename, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category = row["Category"]
            skill = row["Skill"]
            freq = int(row["Freq_Count"])

            if category not in skills:
                skills[category] = []

            skills[category].append({
                "Skill": skill,
                "Freq_Count": freq
            })
    return skills

# =====================================
# PROMPT TEMPLATE (CORE DESIGN)
# =====================================

MARKET_PROMPT = """
You are an expert technical hiring strategist.

Your task:
Select the most appropriate job-market skills for the given user profile,
using ONLY the provided job corpus.

USER PROFILE:
- Role: {role}
- Experience Level: {experience}
- Preparation Time: {months} months
- Study Hours per Day: {hours}
- Other Preferences: {preferences}

IMPORTANT CONSTRAINTS:

1. You may ONLY use skill names exactly as written in the job corpus below.
2. Do NOT invent new skills.
3. Higher Freq_Count indicates stronger market demand.
4. Select ONE dominant backend stack (language + framework).
5. Ensure the skill set is realistic given preparation time.
6. Avoid overloading with multiple unrelated technology stacks.
7. If user has prior familiarity, prefer related technologies when reasonable.

Return STRICT JSON in this format:

{{
  "primary_skills": ["Skill1", "Skill2"],
  "supporting_skills": ["Skill3", "Skill4"],
  "optional_skills": ["Skill5"]
}}

JOB CORPUS:
{corpus}
"""

# =====================================
# MAIN FUNCTION
# =====================================

def generate_market_skills(user_preferences):

    # Select corpus based on location


    # Global_SWE_iter5.json
    # bangladesh_SWE_iter4.json
    if user_preferences["location"].lower() == "Global":
        corpus = load_json_corpus("Global_DataAnalyst_iter6.json")
    else:
        corpus = load_json_corpus("BD_DataAnalyst_iter6.json")

    prompt = MARKET_PROMPT.format(
        role=user_preferences["specific_role"],
        experience=user_preferences["experience_level"],
        months=user_preferences["preparation_time"],
        hours=user_preferences["study_hours"],
        preferences=user_preferences.get("other_preferences", "None"),
        corpus=json.dumps(corpus, indent=2)
    )

    response = llm.generate_content(prompt)
    raw = response.text.strip()

    # Clean markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        raw = raw.replace("json", "", 1)
        raw = raw.rsplit("```", 1)[0]

    parsed = json.loads(raw)

    final_output = {
        "generated_at": datetime.utcnow().isoformat(),
        "user_preferences": user_preferences,
        "market_selected_skills": parsed
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print("✅ Market skill list generated using full corpus reasoning.")
    print(f"📄 Output saved to {OUTPUT_FILE}")

    return final_output

# =====================================
# RUN TEST
# =====================================

if __name__ == "__main__":

    user_preferences = {
        "specific_role": "Data Scientist",  # frontend / backend / full stack
        "experience_level": "University Recent CSE Graduate",        # Beginner / Intermediate / Advanced
        "preparation_time": 6,                 # months
        "study_hours": 2,
        "location": "Global",              # Global / Bangladesh
        "other_preferences": " Love innovtive work, Advanced (Internship / Real-world experience) coding experience, familiar with python, java, C Language and familiar with django,Flask,React,Tensorflow,Pytorch Framework. build some academic, personal and real-world projects.Preferable language is Python."
    }

    generate_market_skills(user_preferences)
