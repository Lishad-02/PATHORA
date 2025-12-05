import json, os
from agent.llm_gemini import call_gemini

def build_curriculum_prompt(skills_data, role):
    return f"""
You are a **Master Curriculum Architect** specializing in {role.replace('_', ' ')} education.

Below is the final, refined skill set from our previous phase:
{json.dumps(skills_data, indent=4)}

🎯 **Goal**
Design a structured learning curriculum that teaches these skills in the most natural dependency order.

📋 **Your tasks**
1. Group all skills into a *logical sequence* that respects prerequisites.
2. For each skill:
   - List 3–6 key **subtopics or competencies**.
   - Assign a **difficulty level** (1=easy to 5=expert).
   - Estimate total **study hours** for an average learner.
   - Identify **depends_on** skills that should come before.
   - Tag importance → `core`, `supporting`, or `advanced`.
3. Add a concise paragraph explaining the ordering rationale.

⚠️ **Output strictly in valid JSON format:**

{{
  "curriculum": [
    {{
      "skill": "C#",
      "subtopics": ["Syntax basics", "OOP fundamentals", "Collections"],
      "difficulty": 3,
      "importance": "core",
      "suggested_hours": 40,
      "depends_on": []
    }},
    {{
      "skill": ".NET Core",
      "subtopics": ["Routing", "Controllers", "Entity Framework"],
      "difficulty": 4,
      "importance": "core",
      "suggested_hours": 50,
      "depends_on": ["C#", "OOP"]
    }}
  ],
  "notes": "Explain how prerequisite ordering was determined."
}}
"""

def build_curriculum(skills_file, role):
    with open(skills_file, "r", encoding="utf-8") as f:
        skills_data = json.load(f)
    prompt = build_curriculum_prompt(skills_data, role)
    result = call_gemini(prompt, temperature=0)
    os.makedirs("outputs", exist_ok=True)
    out = "outputs/phase2_1_curriculum.json"
    with open(out, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"✅ Curriculum built and saved to {out}")
    return result
