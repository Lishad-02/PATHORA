

import os
import google.generativeai as genai

# Try environment, fallback to manual key
api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyA1oFEMts2hb9fp6hRMUjJRbi9PNtalxBw")
genai.configure(api_key=api_key)

def call_gemini(prompt, temperature=0, model="gemini-2.5-flash"):
    model = genai.GenerativeModel(model)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": temperature}
    )
    return response.text

