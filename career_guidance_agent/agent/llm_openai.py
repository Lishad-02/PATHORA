import os
from openai import OpenAI

# Ensure you set: export OPENAI_API_KEY="your-key-here"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_openai(prompt, temperature=0, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content
