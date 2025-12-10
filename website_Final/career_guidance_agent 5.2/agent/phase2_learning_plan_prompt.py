import json, os, re
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_learning_plan_prompt(curriculum_json, time_preference, daily_hours, role):
    return f"""
You are a **Professional Career Mentor** designing a realistic, adaptive learning plan for a {role.replace('_',' ')}.

Here is the structured curriculum you must convert into a time-aware plan:
{curriculum_json}

🕒 Learner constraints:
- Total preparation time: {time_preference}
- Daily study capacity: about {daily_hours} hours/day

🎯 **Your objectives**
1. Convert the curriculum into a **month-by-month** (if {time_preference} ≤ 6 months)  
   or **quarter-by-quarter** (if longer) roadmap.
2. Depth adaptation rules:
   - ≤ 3 months → cover *fundamentals + critical applied subtopics only*.
   - 4-6 months → include *intermediate topics + 1 capstone project*.
   - ≥ 9-12 months → *full advanced coverage + 2-3 projects + soft skills*.
3. Allocate realistic study hours per topic based on {daily_hours} h/day.
4. For each period, include:
   - `theme`
   - `skills_focus`
   - `topics`
   - `estimated_hours`
   - `objectives`
   - `projects`
   - `resources` (types or examples)
5. Finish with motivational tips for sustaining consistency.

⚠️ **Return only valid JSON**:

{{
  "overview": "Short summary of overall plan strategy",
  "plan": [
    {{
      "month": 1,
      "theme": "Fundamentals & Environment Setup",
      "skills_focus": ["C#", "OOP", "Git"],
      "topics": ["Syntax basics", "Classes & objects", "Branching"],
      "estimated_hours": 80,
      "objectives": ["Be able to write structured code in C#"],
      "projects": ["Mini console application"],
      "resources": ["Microsoft Learn C#", "Git-Basics YouTube Course"]
    }},
    ...
  ],
  "tips": [
    "Dedicate last day each week for recap & flashcards",
    "Keep one mini-project active throughout"
  ]
}}
"""

def generate_plan(curriculum_file, time_preference, daily_hours, role):
    with open(curriculum_file, "r", encoding="utf-8") as f:
        curriculum_json = f.read()

    prompt = build_learning_plan_prompt(curriculum_json, time_preference, daily_hours, role)
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content
    match = re.search(r"\{.*\}", text, re.DOTALL)
    plan_json = json.loads(match.group(0)) if match else json.loads(text)

    os.makedirs("outputs", exist_ok=True)
    out = "outputs/phase2_learning_plan.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(plan_json, f, indent=4, ensure_ascii=False)

    print(f"✅ Time-aware learning plan saved to {out}")
    return plan_json
