import json
from pathlib import Path
from datetime import datetime
import google.generativeai as genai

# =====================================
# CONFIGURATION
# =====================================

GEMINI_API_KEY = "AIzaSyDGkpqQymDvRrORFpxQR7bZXveRHMhv1bM"
MODEL_NAME = "models/gemini-2.5-flash"

INPUT_FILE = Path("outputs/step1_generated_skills.json")
OUTPUT_FILE = Path("outputs/structured_curriculum.json")

# -------- USER CONSTRAINTS (SELF-CONTAINED) --------

USER_PROFILE = {
    "role": "Full Stack Developer(Software Engineering)",  # frontend / backend / full stack
    "experience": "University recent CSE graduate",  # Beginner / Intermediate / Advanced
    "preparation_time_months": 12,
    "study_hours_per_day": 8,
    "Market_Focus": "Global",
    "other_preferences": (
        "need fast job, Intermediate (Built small projects) coding experience, familiar with java, C,C++,javascript,typescript,php,kotlin Language and familiar with dot net,node.js,express.js,react framework. build some academic and personal projects & also done intership.preferable language is C# and javascript"
    )
}

# =====================================
# INIT LLM
# =====================================

genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={"temperature": 0}
)

# =====================================
# PROMPT TEMPLATE
# =====================================

# 11,12 point optional 

CURRICULUM_PROMPT = """
You are an Elite Technical Architect and Hiring Committee Lead.

Your mission:
Design a brutal, hiring-optimized technical curriculum that maximizes job-readiness within a strict time constraint. 

This is NOT an academic syllabus. You must architect a production-ready learning path that bridges the gap between a Computer Science degree and real-world industry demands.

USER PROFILE:
- Target Role: {role}
- Experience Level: {experience} (Assume base CSE knowledge: skip basic syntax/loops, focus on architecture, scale, and frameworks)
- Preparation Time: {months} months
- Study Hours per Day: {hours}
- Total Available Study Hours: {total_hours}
- Market Focus: {Market_Focus}
- Other Preferences: {other_preferences}

FINAL SKILL SET TO MASTER:
{final_skills}

STRATEGIC DESIGN PRINCIPLES:

1. The 80/20 Pareto Rule: Focus relentlessly on the 20% of skills that are used 80% of the time in production.
2. Project-Driven Learning: Every module must tie directly to a practical, buildable application. No isolated theoretical modules.
3. Hyper-Personalization: You MUST explicitly justify the technology stack and focus of every module. For each module, generate a targeted rationale explaining exactly how this specific topic leverages the user's `Experience Level` or satisfies their `Other Preferences`. Never select a tool or framework blindly; it must clearly bridge their past experience to their future role.
4. Skip the Basics: Because the user has a CSE background, bypass CS 101 concepts. Jump straight to industry standards (e.g., Object-Relational Mapping, API Security, Advanced Window Functions).
5. Dependency Logic: Respect prerequisite dependencies, but merge lower-impact skills into applied projects to save time.
6. Time Scarcity: Reserve a 10% time buffer. DO NOT exceed available hours.
7. Hiring Weight: Assign a 'hiring_impact' score to each module. This will dictate how much time the user spends practicing it later.


Return STRICT JSON matching the exact structure below. Do not use Markdown wrapping outside the JSON.

{{
  "total_available_hours": 0,
  "estimated_total_required_hours": 0,
  "curriculum_philosophy": "A 2-sentence explanation of why this specific sequence of skills guarantees the highest ROI for this role.",
  "modules": [
    {{
      "module_id": 1,
      "module_name": "e.g., Relational Data & API Architecture",
      "hiring_impact": "High | Medium | Low",
      "difficulty_level": "Intermediate | Advanced",
      "related_skills": ["List of specific skills from the final_skills input"],
      "prerequisites": ["module_ids"],
      "estimated_hours": 0,
      "subtopics": [
        "Include the concept AND the industry standard tool (e.g., 'Authentication via JWT' instead of just 'Security')"
      ],
      "practical_application": "A specific mini-project or feature they must build to prove mastery of this module (e.g., 'Build a rate-limited Node.js API endpoint').",
      "personalization_rationale": "A 1-sentence explanation of exactly why this stack/topic perfectly fits the user's specific background, past research, or preferences.",
      "learning_outcomes": ["Actionable, observable outcomes"]
    }}
  ]
}}
"""

# =====================================
# MAIN FUNCTION
# =====================================

def build_curriculum():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        comparator_output = json.load(f)

    final_skills = comparator_output["recommended_skills"]["skills"]

    total_hours = (
        USER_PROFILE["preparation_time_months"] * 4 * 6 *
        USER_PROFILE["study_hours_per_day"]
    )

    prompt = CURRICULUM_PROMPT.format(
        role=USER_PROFILE["role"],
        experience=USER_PROFILE["experience"],
        months=USER_PROFILE["preparation_time_months"],
        hours=USER_PROFILE["study_hours_per_day"],
        Market_Focus=USER_PROFILE["Market_Focus"],
        other_preferences=USER_PROFILE["other_preferences"],
        total_hours=total_hours,
        final_skills=json.dumps(final_skills, indent=2)
    )

    response = llm.generate_content(prompt)
    raw = response.text.strip()

    if not raw:
      raise ValueError("Empty response from model")

    if raw.startswith("```"):
       raw = raw.split("```", 1)[1]
       if raw.lstrip().startswith("json"):
         raw = raw.lstrip()[4:]
       raw = raw.rsplit("```", 1)[0].strip()

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