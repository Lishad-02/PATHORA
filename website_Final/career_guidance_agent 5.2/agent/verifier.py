import json
import re

def clean_json_output(raw_output: str) -> str:
    """
    Extract JSON from LLM output.
    Handles cases where Gemini/OpenAI add markdown fences or extra text.
    """
    if raw_output is None:
        return "{}"

    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if match:
        return match.group(0).strip()
    
    return raw_output.strip()


def verify_output(raw_output, market_data):
    raw_output = clean_json_output(raw_output)

    try:
        parsed = json.loads(raw_output)
    except Exception as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nRaw Output:\n{raw_output}")

    # Flatten all available skills
    all_skills = set()
    for category, skills in market_data.items():
        # ✅ Skip persona_hint or other string metadata
        if isinstance(skills, dict):
            all_skills.update(skills.keys())

    # Validate only skills present in JSON
    for section in ["core_skills", "optional_skills", "emerging_skills"]:
        valid_list = []
        for item in parsed.get(section, []):
            if isinstance(item, dict) and item.get("name") in all_skills:
                valid_list.append(item)
        parsed[section] = valid_list

    return parsed
