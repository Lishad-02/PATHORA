from openai import OpenAI

# --- Put your API key here directly ---
API_KEY = "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"

client = OpenAI(api_key=API_KEY)

def generate_learning_plan(user_preferences: str):
    """
    Generate an SWE learning plan using GPT-5-mini
    based on multi-sentence user preferences.
    """

    prompt = f"""
You are an expert SWE career mentor.

Task:
- Read the user's multi-sentence preferences.
- Interpret their goals, constraints, background, and preferred role.
- Generate a personalized learning plan for an SWE job.
- Use simple, structured, practical steps.
- Include recommended tools, skills, projects, and timeline.

USER PREFERENCES:
{user_preferences}

OUTPUT FORMAT:
1. Summary of user's goal
2. High-level strategy
3. Detailed month-by-month learning plan
4. Final projects
5. Extra career tips
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a professional SWE mentor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message["content"]


# ------------------------
# Example usage
# ------------------------
if __name__ == "__main__":
    user_input = """
    I want to become a frontend Sosteare engineer.
    I have 5 months.
    I can study 4 hours per day.
   
    """

    plan = generate_learning_plan(user_input)
    print("\n=== GENERATED LEARNING PLAN ===\n")
    print(plan)
