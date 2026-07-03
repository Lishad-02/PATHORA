import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI  # Switched from google.generativeai

# =====================================
# CONFIGURATION
# =====================================

# Replace with your actual OpenAI API Key
OPENAI_API_KEY = "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" 
MODEL_NAME = "gpt-5-mini"

INPUT_FILE = Path("outputs/structured_curriculum_gpt.json")
OUTPUT_FILE = Path("outputs/final_learning_plan_gpt.json")

USER_PROFILE = {
    "role": "AI/ML Engineer",
    "experience": "University CSE graduate",
    "preparation_time_months": 8,
    "study_hours_per_day": 3
}

# =====================================
# INIT LLM
# =====================================

# Initializing the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# =====================================
# PROMPT TEMPLATE (Unchanged)
# =====================================

LEARNING_PLAN_PROMPT = """
You are a senior technical hiring mentor and execution strategist.

Your task:
Transform the structured curriculum into a hiring-optimized execution roadmap.

This is NOT a simple scheduler.
This must maximize real-world employability within the given time constraint.

USER PROFILE:
- Target Role: {role}
- Experience Level: {experience}
- Preparation Time: {months} months
- Study Hours per Day: {hours}
- Total Available Hours: {total_hours}

STRUCTURED CURRICULUM:
{curriculum}

PRIMARY OBJECTIVE:
Maximize hiring probability within the available study time.

EXECUTION STRATEGY RULES:

1. Preserve logical module progression, but you MAY:
   - Merge smaller modules
   - Compress lower-impact topics
   - Reallocate time toward higher hiring impact topics

2. Allocate time based on hiring impact, not equal distribution.

3. Use 90–95% of total available hours. Leave buffer.

4. Avoid overengineering:
   - Do NOT expand into unnecessary enterprise-level depth
   - Do NOT overload advanced topics early

5. Balance FOUR execution tracks (adapt to role automatically):

   A) Core Technical Mastery
   B) Interview / Assessment Preparation (if role requires)
   C) Portfolio / Project Development
   D) Career Execution (resume, LinkedIn, mock interviews, applications)

6. Interview/assessment preparation:
   - Must begin in Month 1 for engineering roles
   - Should increase intensity in later months

7. Portfolio strategy:
   - Projects must start early (not only at the end)
   - Capstone must not be rushed
   - Project work should grow progressively

8. Final month must emphasize:
   - Interview simulation
   - Portfolio polishing
   - Resume and application strategy
   - Mock interviews

9. Weekly workload must realistically align with daily hours.

10. Include a short explanation of why this execution strategy is optimal for the given role and constraints.

Return STRICT JSON:

{{
  "total_available_hours": 0,
  "planned_learning_hours": 0,
  "buffer_hours": 0,
  "execution_strategy_summary": "",
  "monthly_plan": [
    {{
      "month": 1,
      "core_track": [],
      "interview_track": [],
      "portfolio_track": [],
      "career_track": [],
      "estimated_hours": 0,
      "milestone": ""
    }}
  ],
  "final_readiness_summary": ""
}}
"""

# =====================================
# MAIN FUNCTION
# =====================================

def generate_learning_plan():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        curriculum_data = json.load(f)

    curriculum = curriculum_data["curriculum"]
    total_hours = curriculum["total_available_hours"]

    prompt = LEARNING_PLAN_PROMPT.format(
        role=USER_PROFILE["role"],
        experience=USER_PROFILE["experience"],
        months=USER_PROFILE["preparation_time_months"],
        hours=USER_PROFILE["study_hours_per_day"],
        total_hours=total_hours,
        curriculum=json.dumps(curriculum, indent=2)
    )

    # --- UPDATED API CALL ---
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    raw = response.choices[0].message.content.strip()
    # -------------------------

    # Keeping your cleaning logic just in case, 
    # though JSON mode usually removes the need for it.
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        raw = raw.replace("json", "", 1)
        raw = raw.rsplit("```", 1)[0]

    parsed = json.loads(raw)

    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "user_profile": USER_PROFILE,
        "learning_plan": parsed
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("✅ Learning plan generated successfully using GPT-5 Mini.")
    print(f"📄 Output saved to {OUTPUT_FILE}")

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    generate_learning_plan()