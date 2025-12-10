import json, os, re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_time_calibrator_prompt(plan_json, verifier_json, daily_hours, time_preference, role):
    rec = verifier_json.get("time_recommendation", {})
    suggested_hours = rec.get("suggested_daily_hours", "not provided")
    suggested_months = rec.get("suggested_duration_months", "not provided")
    verifier_comment = rec.get("comment", "no specific numeric guidance given")

    return f"""
You are a **Personal Learning Load Optimizer** for {role.replace('_',' ')} training programs.

Below is the verified learning plan and its review:
PLAN:
{json.dumps(plan_json, indent=4)}

REVIEW:
{json.dumps(verifier_json, indent=4)}

User's declared schedule:
- Target duration: {time_preference}
- Average daily study hours: {daily_hours}

Reviewer suggested baseline:
- Recommended daily hours: {suggested_hours}
- Recommended total months: {suggested_months}
- Reviewer note: {verifier_comment}

🎯 **Goal**
Keep the skill set and structure unchanged.
Analyze total learning load and generate *personalized quantitative advice*.

📋 **Your tasks**
1. Estimate total learning load (sum of all month 'estimated_hours' if available, else assume 180 h/month × months).
2. Given {time_preference} and {daily_hours} h/day, calculate the *total available study hours*.
3. Compare both and determine feasibility:
   - realistic  → fits within ±10 %
   - needs more time → workload > available hours × 1.1
   - needs more daily hours → workload > available hours × 1.1 but time is fixed.
4. If not feasible:
   - Compute the **minimum realistic daily hours** if {time_preference} is fixed.
   - Compute the **minimum realistic duration (months)** if {daily_hours} h/day is fixed.
   - Make the numbers concrete (round sensibly).
5. Write a short, friendly **message_to_user** explaining both options clearly.

⚠️ Return strictly valid JSON:
{{
  "feasibility": "realistic / needs more time / needs more daily hours",
  "analysis": "...",
  "recommendation": {{
      "suggested_daily_hours": "X",
      "suggested_duration_months": "Y",
      "message_to_user": "..."
  }}
}}
"""

def calibrate_time(plan_file, verifier_file, daily_hours, time_preference, role):
    # --- Load input files ---
    with open(plan_file, "r", encoding="utf-8") as f:
        plan_json = json.load(f)
    with open(verifier_file, "r", encoding="utf-8") as f:
        verifier_raw = f.read().strip()

    # --- Clean verifier JSON (handle fences like ```json ...) ---
    if verifier_raw.startswith("```"):
        verifier_raw = re.sub(r"^```[a-zA-Z]*\n", "", verifier_raw)
        verifier_raw = verifier_raw.replace("```", "").strip()

    match = re.search(r"\{.*\}", verifier_raw, re.DOTALL)
    if match:
        verifier_raw = match.group(0)

    verifier_json = json.loads(verifier_raw)

    # --- Build prompt ---
    prompt = build_time_calibrator_prompt(plan_json, verifier_json, daily_hours, time_preference, role)

    # --- Call OpenAI GPT-5-Mini ---
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_result = response.choices[0].message.content

    # --- Clean the LLM output ---
    match = re.search(r"\{.*\}", raw_result, re.DOTALL)
    cleaned = match.group(0) if match else raw_result.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {"raw_text": raw_result}

    # --- Save output ---
    os.makedirs("outputs", exist_ok=True)
    out = "outputs/phase2_time_calibration.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=4, ensure_ascii=False)

    print(f"✅ Time-effort calibration saved to {out}")
    return parsed
