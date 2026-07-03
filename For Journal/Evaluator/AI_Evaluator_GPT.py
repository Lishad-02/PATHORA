import json
from datetime import datetime
from openai import OpenAI

# =========================
# Initialize Client
# =========================
# Make sure to replace this with your actual secure API key if sharing the code
client = OpenAI(api_key="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")

# =========================
# USER PREFERENCES
# =========================
user_preferences = {
    "role": "AI Engineer",
    "experience": "University 3rd year CSE Student",
    "preparation_time_months": 6,
    "study_hours_per_day": 3,
    "Market_Focus": "Global",
    "other_preferences": "want a part time job , Basic (Completed some courses / small exercises) coding experience, familiar with python,Java languages and familiar with node.js, React framework. Also build some academic projects, Preferable language is Python"
  
    
}

# =========================
# Load Learning Plans
# =========================
# Ensure these files exist in your directory before running
try:
    with open("plan_1.json", "r") as f:
        plan_1 = json.load(f)

    with open("plan_2.json", "r") as f:
        plan_2 = json.load(f)
except FileNotFoundError as e:
    print(f"Error loading plans: {e}")
    plan_1 = {}
    plan_2 = {}

# =========================
# Evaluation Prompt
# =========================
evaluation_prompt = f"""
You are an expert AI Curriculum Evaluator. Your task is to evaluate two learning plans based strictly on the user's constraints and a specific 7-dimension scoring matrix.

You must strictly follow the scoring rules and limits. If uncertain, give a lower score. Do NOT inflate scores. 

Candidate Preferences:
{json.dumps(user_preferences, indent=2)}

### Scoring Matrix (Total 100 Points):

1. Dimension 1: Hiring Readiness Optimization (HRO) – Max 25
   - Core Technical Readiness (0-8): Covers required stack, appropriate depth.
   - Interview Preparation Readiness (0-8): DSA/System design, Case-study, Behavioral.
   - Portfolio & Project Strength (0-9): Progressive, deployed/real-world, strong capstone.

2. Dimension 2: Time-Constrained Feasibility (TCF) – Max 15
   - Hour Compliance (0-5): Total hours <= available, buffer present.
   - Cognitive Load Realism (0-5): Not overloaded, no unrealistic skill stacking.
   - Overengineering Avoidance (0-5): No unnecessary advanced topics for a short timeline.

3. Dimension 3: Personalization & Preference Alignment (PPA) – Max 15
   - Experience Adaptation (0-5): Beginner reinforcement, graduate depth increase.
   - Preference Integration (0-5): Role-specific, utilizes user preferences.
   - Stack Justification Quality (0-5): Clear reasoning for tech choices.

4. Dimension 4: Market Alignment (MA) – Max 10
   - Skill Demand Relevance (0-5)
   - Regional/Global Alignment (0-5)

5. Dimension 5: Strategic Prioritization Quality (SPQ) – Max 10
   - High-ROI Topics Prioritized (0-5)
   - Logical Phasing (0-5): Foundation -> Applied -> Interview.

6. Dimension 6: Curriculum Structural Depth & Clarity (CSDC) – Max 15
   - Logical Module Ordering (0-5)
   - Meaningful Subtopic Detail (0-5)
   - Clear Learning Outcomes (0-5)

7. Dimension 7: Career Execution Readiness (CER) – Max 10
   - Resume & LinkedIn Preparation (0-4)
   - Mock Interviews Included (0-3)
   - Application Strategy (0-3)

Return ONLY valid JSON.

Required format:
{{
  "Plan_1": {{
    "HRO": {{"score": 0, "breakdown": {{"core_technical": 0, "interview_prep": 0, "portfolio": 0}}, "comment": ""}},
    "TCF": {{"score": 0, "breakdown": {{"hour_compliance": 0, "cognitive_load": 0, "overengineering": 0}}, "comment": ""}},
    "PPA": {{"score": 0, "breakdown": {{"experience_adaptation": 0, "preference_integration": 0, "stack_justification": 0}}, "comment": ""}},
    "MA": {{"score": 0, "breakdown": {{"skill_demand": 0, "global_alignment": 0}}, "comment": ""}},
    "SPQ": {{"score": 0, "breakdown": {{"high_roi": 0, "logical_phasing": 0}}, "comment": ""}},
    "CSDC": {{"score": 0, "breakdown": {{"module_ordering": 0, "subtopic_detail": 0, "learning_outcomes": 0}}, "comment": ""}},
    "CER": {{"score": 0, "breakdown": {{"resume": 0, "mock_interviews": 0, "application_strategy": 0}}, "comment": ""}},
    "Total_Score": 0,
    "overall_summary": ""
  }},
  "Plan_2": {{
    "HRO": {{"score": 0, "breakdown": {{"core_technical": 0, "interview_prep": 0, "portfolio": 0}}, "comment": ""}},
    "TCF": {{"score": 0, "breakdown": {{"hour_compliance": 0, "cognitive_load": 0, "overengineering": 0}}, "comment": ""}},
    "PPA": {{"score": 0, "breakdown": {{"experience_adaptation": 0, "preference_integration": 0, "stack_justification": 0}}, "comment": ""}},
    "MA": {{"score": 0, "breakdown": {{"skill_demand": 0, "global_alignment": 0}}, "comment": ""}},
    "SPQ": {{"score": 0, "breakdown": {{"high_roi": 0, "logical_phasing": 0}}, "comment": ""}},
    "CSDC": {{"score": 0, "breakdown": {{"module_ordering": 0, "subtopic_detail": 0, "learning_outcomes": 0}}, "comment": ""}},
    "CER": {{"score": 0, "breakdown": {{"resume": 0, "mock_interviews": 0, "application_strategy": 0}}, "comment": ""}},
    "Total_Score": 0,
    "overall_summary": ""
  }},
  "comparison": {{
    "better_plan": "Plan_1 or Plan_2",
    "reason": ""
  }}
}}

Learning Plan 1:
{json.dumps(plan_1, indent=2)}

Learning Plan 2:
{json.dumps(plan_2, indent=2)}
"""

# =========================
# Call Model (No temperature)
# =========================
response = client.chat.completions.create(
    model="gpt-5-mini",
    #temperature=0.0,
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": "You are a strict and objective AI Curriculum Evaluator. Always output valid JSON."},
        {"role": "user", "content": evaluation_prompt}
    ]
)

result_text = response.choices[0].message.content

# =========================
# Validate + Save JSON
# =========================
try:
    structured_result = json.loads(result_text)

    # Add metadata
    final_output = {
        "evaluation_metadata": {
            "model_used": "gpt-5-mini",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "candidate_role": user_preferences["role"],
            "preparation_time_months": user_preferences["preparation_time_months"]
        },
        "evaluation_result": structured_result
    }

    # Save nicely formatted JSON
    with open("evaluation_result.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print("✅ Evaluation successfully saved to evaluation_result.json")

except json.JSONDecodeError:
    print("❌ Model did not return valid JSON.")
    print("Raw Output:")
    print(result_text)
