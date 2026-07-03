import json
from pathlib import Path
from datetime import datetime
import google.generativeai as genai

# =====================================
# CONFIGURATION
# =====================================

GEMINI_API_KEY = "AIzaSyAsLsqImXZ4RIFhT5CGKybvEPLCDKYOwtQ"
MODEL_NAME = "models/gemini-2.5-flash"

INPUT_FILE = Path("outputs/structured_curriculum.json")
OUTPUT_FILE = Path("outputs/final_learning_plan3.json")

USER_PROFILE = {
    "role": "Full Stack Developer(Software Engineering)",  # frontend / backend / full stack
    "experience": "University Final Year CSE Student",        # Beginner / Intermediate / Advanced
    "preparation_time_months": 10,
    "study_hours_per_day": 1,
    "Market_Focus": "Global",
    "other_preferences": (
        "looking for remote job, Basic (Completed some courses / small exercises) coding experience, familiar with Python, C, C++, Kotlin and JavaScript and familiar with django,flask framework. Also build some academic project, preferable language is Python"
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

LEARNING_PLAN_PROMPT = """
You are an elite Technical Hiring Mentor and Execution Strategist. 
Your goal is to transition candidates from academic Computer Science backgrounds into production-ready industry roles.

Your task:
Transform the provided structured curriculum into a highly actionable, realistic, and hiring-optimized execution roadmap.

This is NOT a simple syllabus or scheduler. This is a survival guide and execution strategy to maximize real-world employability within strict time constraints. Talk directly to the user in a highly encouraging, mentor-like tone, BUT maintain FAANG-level technical rigor.

USER PROFILE:
- Target Role: {role}
- Experience Level: {experience}
- Preparation Time: {months} months
- Study Hours per Day: {hours}
- Total Available Hours: {total_hours}
- Market Focus: {Market_Focus}
- Other Preferences: {other_preferences}

STRUCTURED CURRICULUM TO ADAPT:
{curriculum}

EXECUTION STRATEGY & REALITY RULES:

1. Time Allocation & Burnout Prevention:
   - Use only 85-90% of total available hours. The remaining 10-15% MUST be allocated as "Buffer Hours" for debugging, life events, and mental rest.
   - Enforce the "70/30 Rule": 30% of time reading/watching tutorials. The remaining 70% must be strictly divided between "Active Practice/Exercises" and "Project/Portfolio Building". Explicitly mention this in your strategy.
   - Implement "Time-Boxing": Advise users not to spend more than a set time on a single bug without moving on or seeking help.
   
2. Anti-"Tutorial Hell" & Portfolio Directives:
   - Explicitly BAN cliché beginner projects (e.g., To-Do lists, basic calculators, Titanic datasets).
   - Portfolio projects must emphasize end-to-end execution: solving real problems, cloud hosting/deployment, and writing professional READMEs.
   - Adaptive Scoping: Base the number of projects strictly on the user's timeline (`months`) and `total_hours`. 
     - If the timeline is short (1-2 months) or hours are low: Focus on exactly ONE high-impact "Iterative Capstone Project" that grows in complexity each week. 
     - If the timeline is longer (3/3+ months) with adequate hours: Plan 1-2 "Skill-Builder Mini-Projects" in early months, culminating in a final Capstone.
   - Enforce Strict MVP Scoping: Explicitly define what features to ignore so the project fits exactly within the allocated time. Avoid scope creep.
   - Projects must start in Month 1 and grow iteratively. Do not leave project work entirely for the end.

3. Track Balancing (Use user-friendly, conversational language):
   - A) Technical Skills to Master: Focus on production-level skills (e.g., REST APIs, cloud databases for SWE; Window functions, dashboards for DA).
   - B) Interview Prep: Shift from pure theory to pattern recognition (Sliding Window, Two Pointers for SWE; SQL case studies for DA). Must begin in Month 1.
   - C) What You'll Build: Iterative project development. 
   - D) Job Hunt Actions: Resume parsing (ATS), cold outreach, LinkedIn optimization, mock behavioral (STAR method).

4. Progression Strategy & Trimming Accountability:
   - Reallocate time toward high hiring-impact topics. Compress low-impact academic topics.
   - Ruthless Trimming with Accountability: If you cut or compress a topic from the provided curriculum to fit the time budget, you MUST document it in the `trimmed_topics_justification` and explain why. Do not drop crucial core skills.
   - Final month MUST be heavily weighted toward Interview Simulation, Portfolio Polishing, and Application Hustle.

5. Granularity & Natural Language Flow:
   - Break down each month into clear "Weekly Micro-Goals".
   - You MUST write in natural, conversational English. Avoid robotic, disjointed bullet points. Write full, easy-to-read sentences that flow well (e.g., instead of "Learn SQL," write "This week, you'll dive into SQL window functions so you can analyze complex user data sets.").

6. Hyper-Personalized Delivery:
   - You MUST extract and synthesize the `personalization_rationale` provided in the inputted curriculum modules.
   - Explicitly remind the user *why* this specific plan leverages their unique background, preferences, or past academic experience to give them an unfair advantage.

7. The "Human Mentor" Voice (Warm Delivery, Brutal Standards):
   - Speak directly to the user using "You" and "We". Be warm and empathetic, but do not compromise the technical bar just to be nice. The plan must make them undeniably hireable.
   - Preemptively acknowledge when a topic is notoriously difficult. Tell them it's normal to struggle.
   
8. Resource Curation (Anti-Hallucination):
   - For every month, provide 2-3 highly specific, gold-standard resources (Videos, Docs, or Interactive Platforms).
   - DO NOT generate URLs as they may hallucinate. Instead, provide the exact creator name, channel, or search term (e.g., "Official Next.js Documentation", or "NeetCode Two-Pointer Playlist on YouTube").

Return STRICT JSON matching the exact structure below. Do not use Markdown wrapping outside the JSON.

{{
  "total_available_hours": 0,
  "planned_learning_hours": 0,
  "buffer_hours": 0,
  "execution_strategy_summary": "A 3-4 sentence personalized pitch explaining exactly how this specific execution plan leverages their background and preferences to make them highly competitive for the target role.",
  "monthly_plan": [
    {{
      "month": 1,
      "theme": "e.g., The Baseline & Backend Foundations",
      "weekly_micro_goals": [
        "Week 1: [Conversational, full sentence explaining the micro-goal]",
        "Week 2: [Conversational, full sentence explaining the micro-goal]",
        "Week 3: [Conversational, full sentence explaining the micro-goal]",
        "Week 4: [Conversational, full sentence explaining the micro-goal]"
      ],
      "time_budget_hours": {{
        "total_monthly_hours": 0,
        "theory_and_reading": 0,
        "active_practice_and_coding": 0,
        "portfolio_project_building": 0
      }},
      "technical_skills_to_master": ["Conversational, plain-English technical goals"],
      "interview_prep_goals": ["Conversational prep goals"],
      "what_you_will_build": ["Conversational explanation of the specific project features they will build this month"],
      "job_hunt_action_items": ["Conversational career prep actions"],
      "curated_resources": [
        {{
          "topic": "e.g., Advanced React",
          "resource_type": "YouTube Video | Official Docs | Interactive Platform",
          "recommended_search_term": "e.g., 'Traversy Media React Crash Course' (Do not use fake URLs)"
        }}
      ],
      "milestone_deliverable": "One tangible thing they MUST have built or achieved by the end of this month."
    }}
  ],
  "critical_guidelines": [
    "List 3-5 hard rules for the user to survive this plan (e.g., 70/30 rule, time-boxing). Write these as direct, encouraging advice."
  ],
  "final_readiness_summary": "A highly motivational summary of what the candidate will look like to a recruiter after completing this plan, explicitly referencing their unique background combined with their new skills."
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
        Market_Focus=USER_PROFILE["Market_Focus"],
        other_preferences=USER_PROFILE["other_preferences"],
        total_hours=total_hours,
        curriculum=json.dumps(curriculum, indent=2)
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
        "learning_plan": parsed
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("✅ Learning plan generated successfully.")
    print(f"📄 Output saved to {OUTPUT_FILE}")

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    generate_learning_plan()