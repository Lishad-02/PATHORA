import json
import os
import re
from agent.llm_gemini import call_gemini


def personalize_skills(cleaned_file: str, known_skills: list):
    """
    Removes already-known skills from the user's cleaned skill list using Gemini.
    Keeps all structure and information intact.

    Args:
        cleaned_file (str): Path to phase1_6_cleaned.json
        known_skills (list): List of skills user already knows

    Returns:
        dict: Updated JSON with known skills removed
    """

    # Load JSON
    with open(cleaned_file, "r", encoding="utf-8") as f:
        skills_data = json.load(f)

    # Prepare prompt
    prompt = f"""
You are a precise JSON editor.

Below is the current skill recommendation JSON:
{json.dumps(skills_data, indent=4)}

The user already knows the following skills:
{known_skills}

Your task:
1. Remove only the entries whose "name" exactly matches any of the skills above (case-insensitive).
2. Keep all other skills, reasons, and nested structure **exactly the same**.
3. Maintain valid JSON and identical field names.
4. Return only valid JSON (no explanations).

Example transformation:
Input: {{ "core_skills": {{ "fundamentals": [{{"name": "HTML"}}, {{"name": "CSS"}}, {{"name": "JS"}}] }} }}
Known: ["HTML"]
Output: {{ "core_skills": {{ "fundamentals": [{{"name": "CSS"}}, {{"name": "JS"}}] }} }}
"""

    # Call Gemini model
    result = call_gemini(prompt, temperature=0)

    # Extract JSON
    match = re.search(r"\{.*\}", result, re.DOTALL)
    cleaned_json_str = match.group(0) if match else result.strip()

    try:
        updated_data = json.loads(cleaned_json_str)
    except json.JSONDecodeError:
        print("⚠️ Could not parse LLM output as JSON. Keeping original data.")
        updated_data = skills_data

    # Save updated version
    os.makedirs("outputs", exist_ok=True)
    with open(cleaned_file, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=4, ensure_ascii=False)

    # Save known skills separately
    known_file = "outputs/known_skills.json"
    with open(known_file, "w", encoding="utf-8") as f:
        json.dump({"known_skills": known_skills}, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Updated skill list saved to {cleaned_file}")
    print(f"🗂️  Known skills saved to {known_file}")

    return updated_data
