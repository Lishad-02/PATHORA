import json
from pathlib import Path
from datetime import datetime
import google.generativeai as genai

# =====================================
# CONFIGURATION
# =====================================

GEMINI_API_KEY = "AIzaSyDGkpqQymDvRrORFpxQR7bZXveRHMhv1bM"
MODEL_NAME = "models/gemini-2.5-flash"

INPUT_FILE = Path("outputs/final_comparator_output.json")
OUTPUT_FILE = Path("outputs/structured_curriculum.json")

# -------- USER CONSTRAINTS (SELF-CONTAINED) --------

USER_PROFILE = {
    "role": "Machine Learning Engineer",  # frontend / backend / full stack
    "experience": "University Final Year CSE student",
    "preparation_time_months": 8,
    "study_hours_per_day": 4,
    "other_preferences": (
        " Intermediate programming experience, comfortable with python, java,c and 2 more language, familiar with node.js,express.js,pytorch framework, prefere python as main language,prefer practical learning"
    )
}

# =====================================
# INIT LLM
# =====================================

genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel(MODEL_NAME)

# =====================================
# PROMPT TEMPLATE
# =====================================

# 11,12 point optional 

CURRICULUM_PROMPT = """
You are a senior technical career strategist and curriculum architect.

Your mission:
Design a hiring-optimized curriculum that maximizes job-readiness within the given time constraint.

This is NOT an academic syllabus.
It must strategically prepare the learner for real-world hiring.

USER PROFILE:
- Target Role: {role}
- Experience Level: {experience}
- Preparation Time: {months} months
- Study Hours per Day: {hours}
- Total Available Study Hours: {total_hours}
- Other Preferences: {other_preferences}

FINAL SKILL SET:
{final_skills}

PRIMARY OBJECTIVE:
Maximize employability within the available study time.

STRATEGIC DESIGN PRINCIPLES:

1. Organize skills into logically ordered modules.
2. Respect prerequisite dependencies.
3. Ensure progressive difficulty (Foundation → Applied → Advanced).
4. Allocate time based on real-world hiring importance.
5. You MAY compress or merge lower-impact skills if needed.
6. Do NOT exceed available study hours.
7. Reserve 5–10% time buffer.
8. Avoid overengineering for limited timelines.
9. Balance:
   - Core technical mastery
   - Interview/assessment preparation (if role requires)
   - Practical project readiness
10. If experience level = Beginner, reinforce fundamentals before advanced stack topics.
11. If experience level = Graduate/Intermediate, increase interview depth.
12. Maintain stack coherence (do not mix conflicting technologies).

CRITICAL THINKING RULE:
Prioritize what improves hiring probability over what increases theoretical completeness.

Return STRICT JSON:

{{
  "total_available_hours": 0,
  "estimated_total_required_hours": 0,
  "modules": [
    {{
      "module_id": 1,
      "module_name": "",
      "difficulty_level": "",
      "related_skills": [],
      "prerequisites": [],
      "estimated_hours": 0,
      "subtopics": [],
      "learning_outcomes": []
    }}
  ],
  "curriculum_summary": ""
}}
"""

# =====================================
# MAIN FUNCTION
# =====================================

def build_curriculum():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        comparator_output = json.load(f)

    final_skills = comparator_output["final_skill_decision"]

    total_hours = (
        USER_PROFILE["preparation_time_months"] * 4 * 6 *
        USER_PROFILE["study_hours_per_day"]
    )

    prompt = CURRICULUM_PROMPT.format(
        role=USER_PROFILE["role"],
        experience=USER_PROFILE["experience"],
        months=USER_PROFILE["preparation_time_months"],
        hours=USER_PROFILE["study_hours_per_day"],
        other_preferences=USER_PROFILE["other_preferences"],
        total_hours=total_hours,
        final_skills=json.dumps(final_skills, indent=2)
    )

    response = llm.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        raw = raw.replace("json", "", 1)
        raw = raw.rsplit("```", 1)[0]

    parsed = json.loads(raw)

    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "user_profile": USER_PROFILE,
        "curriculum": parsed
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("✅ Curriculum successfully generated.")
    print(f"📄 Output saved to {OUTPUT_FILE}")

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    build_curriculum()