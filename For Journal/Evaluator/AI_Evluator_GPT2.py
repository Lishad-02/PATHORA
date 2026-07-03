import json
import os
import time
from datetime import datetime
from openai import OpenAI

# =========================
# Configuration
# =========================
client = OpenAI(api_key="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")
MODEL = "gpt-4o-2024-08-06"
TEMPERATURE = 0.5
PROMPT_VERSION = "v1.0"

# =========================
# Dimension Maximums
# =========================
DIMENSION_MAXES = {
    "HRO":  {"max": 25, "breakdown": {"core_technical": 8, "interview_prep": 8, "portfolio": 9}},
    "TCF":  {"max": 15, "breakdown": {"hour_compliance": 5, "cognitive_load": 5, "overengineering": 5}},
    "PPA":  {"max": 15, "breakdown": {"experience_adaptation": 5, "preference_integration": 5, "stack_justification": 5}},
    "MA":   {"max": 10, "breakdown": {"skill_demand": 5, "global_alignment": 5}},
    "SPQ":  {"max": 10, "breakdown": {"high_roi": 5, "logical_phasing": 5}},
    "CSDC": {"max": 15, "breakdown": {"module_ordering": 5, "subtopic_detail": 5, "learning_outcomes": 5}},
    "CER":  {"max": 10, "breakdown": {"resume": 4, "mock_interviews": 3, "application_strategy": 3}}
}

# =========================
# User Preferences
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
# Single-Plan Evaluation Prompt
# =========================
EVALUATION_PROMPT = """
You are a strict AI Curriculum Evaluator. Evaluate the learning plan below 
against the user's profile using the 7-dimension HROP scoring matrix.

IMPORTANT RULES:
- Evaluate this plan INDEPENDENTLY against the rubric. Do NOT compare to any other plan.
- Do NOT inflate scores. If uncertain, score lower.
- Breakdown scores MUST sum exactly to the dimension total.
- No subcriterion may exceed its stated maximum.
- Return ONLY valid JSON. No explanation outside the JSON.

USER PROFILE:
{user_preferences}

SCORING MATRIX:
1. HRO — Hiring Readiness Optimization (Max 25)
   - core_technical (0-8): Covers required stack, appropriate depth
   - interview_prep (0-8): DSA/system design, case-study, behavioral
   - portfolio (0-9): Progressive projects, deployed/real-world, strong capstone

2. TCF — Time-Constrained Feasibility (Max 15)
   - hour_compliance (0-5): Total hours within budget, buffer present
   - cognitive_load (0-5): Not overloaded, no unrealistic skill stacking
   - overengineering (0-5): No unnecessary advanced topics for timeline

3. PPA — Personalization & Preference Alignment (Max 15)
   - experience_adaptation (0-5): Appropriate for stated experience level
   - preference_integration (0-5): Reflects role and user preferences
   - stack_justification (0-5): Clear reasoning for technology choices

4. MA — Market Alignment (Max 10)
   - skill_demand (0-5): Skills match current job market demand
   - global_alignment (0-5): Relevant to global market focus

5. SPQ — Strategic Prioritization Quality (Max 10)
   - high_roi (0-5): High-impact topics covered first
   - logical_phasing (0-5): Foundation -> Applied -> Interview progression

6. CSDC — Curriculum Structural Depth & Clarity (Max 15)
   - module_ordering (0-5): Logical prerequisite-respecting order
   - subtopic_detail (0-5): Meaningful detail, not verbose filler
   - learning_outcomes (0-5): Clear, observable, actionable outcomes

7. CER — Career Execution Readiness (Max 10)
   - resume (0-4): Resume and LinkedIn preparation included
   - mock_interviews (0-3): Mock interview practice included
   - application_strategy (0-3): Job application strategy included

REQUIRED JSON FORMAT:
{{
  "HRO":  {{"score": 0, "breakdown": {{"core_technical": 0, "interview_prep": 0, "portfolio": 0}}, "comment": ""}},
  "TCF":  {{"score": 0, "breakdown": {{"hour_compliance": 0, "cognitive_load": 0, "overengineering": 0}}, "comment": ""}},
  "PPA":  {{"score": 0, "breakdown": {{"experience_adaptation": 0, "preference_integration": 0, "stack_justification": 0}}, "comment": ""}},
  "MA":   {{"score": 0, "breakdown": {{"skill_demand": 0, "global_alignment": 0}}, "comment": ""}},
  "SPQ":  {{"score": 0, "breakdown": {{"high_roi": 0, "logical_phasing": 0}}, "comment": ""}},
  "CSDC": {{"score": 0, "breakdown": {{"module_ordering": 0, "subtopic_detail": 0, "learning_outcomes": 0}}, "comment": ""}},
  "CER":  {{"score": 0, "breakdown": {{"resume": 0, "mock_interviews": 0, "application_strategy": 0}}, "comment": ""}},
  "Total_Score": 0,
  "overall_summary": ""
}}

LEARNING PLAN TO EVALUATE:
{plan}
"""

# =========================
# Validation
# =========================
def validate_scores(result, plan_label):
    errors = []
    total_check = 0
    for dim, limits in DIMENSION_MAXES.items():
        score = result[dim]["score"]
        if score > limits["max"]:
            errors.append(f"{dim}: score {score} exceeds max {limits['max']}")
        breakdown_sum = sum(result[dim]["breakdown"].values())
        if breakdown_sum != score:
            errors.append(f"{dim}: breakdown sum {breakdown_sum} != score {score}")
        for sub, sub_max in limits["breakdown"].items():
            sub_score = result[dim]["breakdown"].get(sub, 0)
            if sub_score > sub_max:
                errors.append(f"{dim}.{sub}: {sub_score} exceeds max {sub_max}")
        total_check += score
    if result.get("Total_Score", 0) != total_check:
        errors.append(f"Total_Score {result['Total_Score']} != {total_check}")
    return errors

# =========================
# Evaluate Single Plan
# =========================
def evaluate_single_plan(plan, plan_label, user_preferences, max_retries=3):
    prompt = EVALUATION_PROMPT.format(
        user_preferences=json.dumps(user_preferences, indent=2),
        plan=json.dumps(plan, indent=2)
    )
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", 
                     "content": "You are a strict AI Curriculum Evaluator. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            errors = validate_scores(result, plan_label)
            
            if errors:
                print(f"  Attempt {attempt+1} validation errors: {errors}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    print(f"  WARNING: {plan_label} has unresolved validation errors")
            
            return result, response
            
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    
    return None, None

# =========================
# Main
# =========================
def main():
    # Load plans
    try:
        with open("plan_1.json", "r") as f:
            plan_1 = json.load(f)
        with open("plan_2.json", "r") as f:
            plan_2 = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    print("Evaluating Plan 1...")
    result_1, response_1 = evaluate_single_plan(plan_1, "Plan_1", user_preferences)
    
    print("Evaluating Plan 2...")
    result_2, response_2 = evaluate_single_plan(plan_2, "Plan_2", user_preferences)

    if result_1 is None or result_2 is None:
        print("Evaluation failed. Check errors above.")
        return

    # Determine better plan
    better = "Plan_1" if result_1["Total_Score"] >= result_2["Total_Score"] else "Plan_2"

    final_output = {
        "evaluation_metadata": {
            "model_used": response_1.model,
            "prompt_version": PROMPT_VERSION,
            "temperature": TEMPERATURE,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "candidate_role": user_preferences["role"],
            "preparation_time_months": user_preferences["preparation_time_months"],
            "evaluation_type": "independent_per_plan",
            "tokens": {
                "plan1_prompt": response_1.usage.prompt_tokens,
                "plan1_completion": response_1.usage.completion_tokens,
                "plan2_prompt": response_2.usage.prompt_tokens,
                "plan2_completion": response_2.usage.completion_tokens,
            }
        },
        "Plan_1": result_1,
        "Plan_2": result_2,
        "comparison": {
            "better_plan": better,
            "Plan_1_Total": result_1["Total_Score"],
            "Plan_2_Total": result_2["Total_Score"],
            "score_difference": abs(result_1["Total_Score"] - result_2["Total_Score"])
        }
    }

    with open("evaluation_result2.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"\nPlan 1 Total: {result_1['Total_Score']}/100")
    print(f"Plan 2 Total: {result_2['Total_Score']}/100")
    print(f"Better Plan: {better}")
    print("Saved to evaluation_result.json")

if __name__ == "__main__":
    main()