#AIzaSyA1oFEMts2hb9fp6hRMUjJRbi9PNtalxBw

import google.generativeai as genai
import json

# 🔑 Insert your Gemini API key here
GEMINI_API_KEY = "AIzaSyAsLsqImXZ4RIFhT5CGKybvEPLCDKYOwtQ"

genai.configure(api_key=GEMINI_API_KEY)


# ============================================================
# BL-1: Naive User Baseline Prompt
# Simulates exactly what a real user would type into an LLM.
# No prompt engineering. No structure. No expert guidance.
# ============================================================
NAIVE_USER_BASELINE_PROMPT = """
I want to become a {role}. I have {months} months to prepare and I can study {hours} hours per day. 
My experience level is {experience}. My background includes {other_preferences}
Now generate a comprehensive learning plan that will make me as job-ready as possible for the market.
"""


def generate_baseline_plan(
    role: str,
    months: int,
    hours: float,
    experience: str,
    other_preferences: str = ""
) -> dict:

    prompt = NAIVE_USER_BASELINE_PROMPT.format(
        role=role,
        months=months,
        hours=hours,
        experience=experience,
        other_preferences=other_preferences
    )

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    
    # Enforce JSON output from the model to avoid unstructured text
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    # Parse the model's JSON string into a Python dictionary
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"raw_text": response.text}


# ------------------------
# Example usage
# ------------------------
if __name__ == "__main__":

    # --- User inputs (same inputs fed to your main system for fair comparison) ---
    role              = "Machine Learning Engineer"
    months            = 8
    hours             = 4
    experience        = "University Final Year CSE Student"
    other_preferences = (
        "Want to focus Global Market,Intermediate (Built small projects) coding experience, familiar with python, java, C, C++ Language and familiar with node.js,Express.js,Pytorch Framework. build some academic projects. prefer python languge and practical learning"
    )


    # --- Generate BL-1 output ---
    plan_json = generate_baseline_plan(
        role=role,
        months=months,
        hours=hours,
        experience=experience,
        other_preferences=other_preferences
    )

    print("\n=== BL-1: NAIVE USER BASELINE LEARNING PLAN ===\n")
    print(json.dumps(plan_json, indent=4))

    # --- Save to JSON ---
    output_data = {
        "b1": "B1_ZS",
        "model": "gemini-2.5-flash",
        "user_profile": {
            "role": role,
            "months": months,
            "hours_per_day": hours,
            "experience": experience,
            "other_preferences": other_preferences
        },
        "prompt_used": NAIVE_USER_BASELINE_PROMPT.format(
            role=role,
            months=months,
            hours=hours,
            experience=experience,
            other_preferences=other_preferences
        ),
        "generated_plan": plan_json  # This is now a clean JSON object instead of a string
    }

    with open("bl1.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    print("\n✅ BL-1 baseline plan saved to bl1_naive_baseline.json")