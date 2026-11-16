import json
import os


def load_market_data(region="global", role="software_engineer", persona=None):
    """
    Load skill frequency data based on job role, region, and specialization persona.
    Supported roles: 'software_engineer', 'data_analyst'
    """

    region = region.lower()
    role = role.lower().replace(" ", "_")
    persona_key = (persona or "").lower().strip()

    # --- Choose file based on role and region ---
    if role in ["software_engineer", "swe"]:
        if region in ["bd", "bangladesh"]:
            file_path = os.path.join("data", "Bangladesh_SWE_iter4.json")
        else:
            file_path = os.path.join("data", "Global_SWE_iter5.json")

        # Different persona filters (useful for prompt conditioning)
        print(f"📊 Loading data for {persona_key or 'general SWE'} ({region}) market")

    elif role in ["data_analyst", "analyst"]:
        if region in ["bd", "bangladesh"]:
            file_path = os.path.join("data", "Global_DataAnalyst_iter6.json")
        else:
            file_path = os.path.join("data", "Global_DataAnalyst_iter6.json")
        print(f"📊 Loading data for Data Analyst ({region}) market")

    else:
        raise ValueError(f"Unsupported role: {role}")

    # --- Load and normalize JSON ---
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    normalized = {}
    for category, skills in raw_data.items():
        if isinstance(skills, list):
            skill_dict = {}
            for s in skills:
                if isinstance(s, dict) and "Skill" in s and "Freq_Count" in s:
                    skill_dict[s["Skill"]] = s["Freq_Count"]
            normalized[category] = skill_dict
        else:
            normalized[category] = skills

    # Inject persona hint (so later prompts can adjust skill bias)
    normalized["persona_hint"] = persona_key or "general"

    return normalized
