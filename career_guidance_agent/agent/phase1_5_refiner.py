import json 
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_refine_prompt(skills_data, time_preference, role="software_engineer"):
    """
    Build the prompt for OpenAI refiner that checks time feasibility,
    reduces the skill set intelligently, and reorganizes skills into
    detailed categories for better user clarity.
    """

    # Dynamically adjust based on role
    if role.lower() in ["data_analyst", "analyst"]:
        job_title = "Data Analyst"
        examples = "data cleaning, visualization, SQL, statistics, Power BI/Tableau, and reporting automation"
        tech_areas = "fundamentals, data analysis, visualization, database querying, and reporting tools"
    else:
        job_title = "Software Engineering"
        examples = "backend frameworks, databases, version control, testing, and deployment"
        tech_areas = "fundamentals, backend, database, cloud, and architecture"

    return f"""
You are a Senior Career Guidance Expert specializing in {job_title} job preparation.
The user has {time_preference} to become job-ready.

Below is their initially recommended skill set (grouped into core, optional, and emerging):
{json.dumps(skills_data, indent=4)}

Your task:
1. Assess if this entire skill set is realistic to master within {time_preference}.
2. If the skill set is too large, reduce it intelligently:
   - Keep balance across different technical areas ({tech_areas}).
   - Merge or drop redundant or overlapping skills.
   - Prioritize the most essential and high-impact skills for employability.
   - Keep only what ensures realistic job-readiness within the timeframe.
3. Reorganize the refined skills into *detailed, user-friendly categories*:

   **Core Skills** → fundamentals, frameworks, databases, version control  
   **Supporting Skills** → testing, APIs, debugging, DevOps/cloud basics  
   **Advanced Skills** → architecture, scalability, AI or analytics integration  
   **Professional Skills** → teamwork, communication, agile workflow, problem-solving mindset

4. For every retained skill, add a short reason and mark whether it was kept or removed.
5. Summarize overall reasoning for feasibility and reduction decisions.

Return strictly in valid JSON format:

{{
  "feasibility": "Yes" or "No",
  "reasoning": "...",
  "core_skills": {{
      "fundamentals": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "frameworks_and_runtime": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "databases": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "version_control_and_ci_cd": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}]
  }},
  "supporting_skills": {{
      "testing_and_debugging": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "api_and_networking": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "deployment_and_cloud": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}]
  }},
  "advanced_skills": {{
      "architecture_and_design": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "data_and_ai_integration": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "security_and_scalability": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}]
  }},
  "professional_skills": {{
      "communication": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "project_management": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}],
      "problem_solving": [{{"name": "...", "reason": "...", "kept_or_removed": "kept/removed"}}]
  }}
}}
"""

def call_openai_refiner(prompt, model="gpt-5-mini"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def clean_json_output(raw_output):
    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    return match.group(0).strip() if match else raw_output.strip()


def refine_skills(input_file, time_preference, model="gpt-5-mini", role="software_engineer"):
    """
    Main function to load Phase 1 output and run OpenAI refinement.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        skills_data = json.load(f)

    prompt = build_refine_prompt(skills_data, time_preference, role)
    raw_output = call_openai_refiner(prompt, model=model)
    cleaned_output = clean_json_output(raw_output)

    try:
        parsed = json.loads(cleaned_output)
    except Exception as e:
        print("Error parsing output:", e)
        print("Raw output:\n", raw_output)
        return None

    refined_file = "outputs/phase1_5_refined.json"
    os.makedirs("outputs", exist_ok=True)
    with open(refined_file, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Refined skill set saved to {refined_file}")
    return parsed

