from openai import OpenAI  # Switched from google.generativeai

# 🔑 Put your OpenAI API key here directly
OPENAI_API_KEY = "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"

# Initializing the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_learning_plan(user_preferences: str):
    prompt = f"""
You are an expert SWE career mentor.

Task: Create a personalized for the user based on their preferences.

USER PREFERENCES:
{user_preferences}
"""

    # Updated to OpenAI chat completion format
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


# ------------------------
# Example usage
# ------------------------
if __name__ == "__main__":
    user_input = """
    I want to become a AI/Ml engineer for the global job market.
    I have 8 months.i am university cse graduate.
    I can study 3 hours per day.I expert in python.
    """

    plan = generate_learning_plan(user_input)
    print("\n=== GENERATED LEARNING PLAN ===\n")
    print(plan)