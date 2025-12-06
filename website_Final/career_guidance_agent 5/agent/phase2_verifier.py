import json, os, re
from agent.llm_gemini import call_gemini

def build_verifier_prompt(plan_json, role, time_preference=None, daily_hours=None):
    return f"""
You are a **Curriculum Quality Reviewer** for {role.replace('_',' ')} training programs.

Below is the proposed learning plan:
{json.dumps(plan_json, indent=4)}

User context:
- Declared total preparation time: {time_preference or "Not specified"}
- Declared average daily study hours: {daily_hours or "Not specified"}

Evaluate the plan for:
1. **Feasibility:** Is the pacing realistic for {time_preference} with about {daily_hours} hours/day?
2. **Completeness:** Are all major required skills for job readiness covered proportionally?
3. **Realism:** Does the month-wise time allocation match the depth required for mastery?
4. **Improvement:** If pacing is unrealistic, suggest clear, *quantitative* guidance such as:
   - “Increase to X hours/day” or
   - “Extend to Y months”.

Respond in **pure JSON** format only:

{{
  "verdict": "realistic / too fast / too shallow / unbalanced",
  "reasoning": "...",
  "suggested_revisions": ["..."],
  "time_recommendation": {{
    "suggested_daily_hours": "...",
    "suggested_duration_months": "...",
    "comment": "..."
  }}
}}
"""

def verify_plan(plan_file, role, time_preference=None, daily_hours=None):
    # Load plan
    with open(plan_file, "r", encoding="utf-8") as f:
        plan_json = json.load(f)

    # Build and call Gemini
    prompt = build_verifier_prompt(plan_json, role, time_preference, daily_hours)
    raw_result = call_gemini(prompt, temperature=0)

    # --- 🧹 Clean Gemini output before saving ---
    match = re.search(r"\{.*\}", raw_result, re.DOTALL)
    cleaned = match.group(0) if match else raw_result.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("⚠️ Could not parse verifier output as JSON. Saving raw text instead.")
        parsed = {"raw_text": raw_result}

    # Save clean JSON
    os.makedirs("outputs", exist_ok=True)
    out = "outputs/phase2_verified.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=4, ensure_ascii=False)

    print(f"✅ Plan verification report saved to {out}")
    return parsed
