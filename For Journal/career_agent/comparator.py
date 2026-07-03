import json
from pathlib import Path
from datetime import datetime
import google.generativeai as genai

# =====================================
# CONFIGURATION (SELF-CONTAINED)
# =====================================

GEMINI_API_KEY = "AIzaSyAsLsqImXZ4RIFhT5CGKybvEPLCDKYOwtQ"
MODEL_NAME = "models/gemini-2.5-flash"

LLM_A_FILE = Path("outputs/step1_generated_skills.json")
LLM_B_FILE = Path("outputs/stepB_market_skills.json")
OUTPUT_FILE = Path("outputs/final_comparator_output.json")

# ----------- USER CONSTRAINTS (DIRECTLY DEFINED HERE) ------------

USER_PROFILE = {
    "role": "Machine Learning Engineer",  # frontend / backend / full stack
    "experience": "University Final Year CSE Student",
    "preparation_time_months": 8,
    "study_hours_per_day": 4,
    "Market_Focus": "Global",
    "other_preferences": "Intermediate (Built small projects) coding experience, familiar with python, java, C, C++ Language and familiar with node.js,Express.js,Pytorch Framework. build some academic projects. prefer python languge and practical learning"
}

# =====================================
# INIT LLM
# =====================================

genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel(MODEL_NAME)

# =====================================
# COMPARATOR PROMPT
# =====================================

COMPARATOR_PROMPT = """
You are an expert technical career strategist.

Your task:
Reconcile two skill lists into a single coherent, realistic, and market-aware skill roadmap.

INPUT 1 — Learner-Centric Skills:
{learner_skills}

INPUT 2 — Market-Centric Skills:
{market_skills}

USER PROFILE:
- Role: {role}
- Experience Level: {experience}
- Preparation Time: {months} months
- Study Hours per Day: {hours}
- Market Focus: {Market_Focus}
- Other Preferences: {preferences}

DECISION FRAMEWORK:

Step 1:
Identify the dominant backend stack (language + framework) in each list.

Step 2:
Evaluate whether switching stacks is justified considering:
- preparation time
- experience level
- learning cost
- prior familiarity

Step 3:
Construct a final skill list that:
- Preserves internal stack coherence
- Uses only skills from the two provided lists
- Limits primary technologies to a realistic number
- Keeps foundational learner skills
- Moderates market-only skills based on feasibility

STRICT RULES:
1. Do NOT introduce new skills.
2. Do NOT combine multiple unrelated primary stacks.
3. Keep the plan realistic for the given preparation time.
4. Provide a short explanation of stack decision.

Return STRICT JSON:

{{
  "primary_skills": [],
  "supporting_skills": [],
  "optional_skills": [],
  "excluded_skills": [],
  "stack_decision_summary": ""
}}
"""

# =====================================
# MAIN COMPARATOR LOGIC
# =====================================

def run_comparator():

    with open(LLM_A_FILE, "r", encoding="utf-8") as f:
        llm_a = json.load(f)

    with open(LLM_B_FILE, "r", encoding="utf-8") as f:
        llm_b = json.load(f)

    learner_skills = llm_a["recommended_skills"]["skills"]
    market_skills = llm_b["market_selected_skills"]

    prompt = COMPARATOR_PROMPT.format(
        learner_skills=json.dumps(learner_skills, indent=2),
        market_skills=json.dumps(market_skills, indent=2),
        role=USER_PROFILE["role"],
        experience=USER_PROFILE["experience"],
        months=USER_PROFILE["preparation_time_months"],
        hours=USER_PROFILE["study_hours_per_day"],
        Market_Focus=USER_PROFILE["Market_Focus"],
        preferences=USER_PROFILE["other_preferences"]
    )

    response = llm.generate_content(prompt)
    raw = response.text.strip()

    # Clean markdown if present
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        raw = raw.replace("json", "", 1)
        raw = raw.rsplit("```", 1)[0]

    parsed = json.loads(raw)

    final_output = {
        "generated_at": datetime.utcnow().isoformat(),
        "user_profile": USER_PROFILE,
        "final_skill_decision": parsed
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print("✅ Comparator completed successfully.")
    print(f"📄 Output saved to {OUTPUT_FILE}")

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    run_comparator()
