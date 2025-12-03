# llm/llm_client.py

import os
from openai import OpenAI
import google.generativeai as genai


class LLMClient:
    def __init__(self, provider: str, model: str):
        """
        provider: "openai" or "gemini"
        model: model name string
        """
        self.provider = provider
        self.model = model

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("ERROR: OPENAI_API_KEY not found in environment variables.")
            self.client = OpenAI(api_key=api_key)

        elif provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("ERROR: GEMINI_API_KEY not found in environment variables.")
            genai.configure(api_key=api_key)
            self.client = genai

        else:
            raise ValueError(f"Invalid provider: {provider}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        A universal wrapper that returns the raw text content from either:
        - OpenAI Responses API
        - Google Gemini 2.5 Flash
        """
        if self.provider == "openai":
            resp = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            # Robust extraction for modern Responses API
            try:
                if hasattr(resp, "output_text") and resp.output_text:
                    return resp.output_text

                if hasattr(resp, "output_text_array") and resp.output_text_array:
                    return "\n".join(resp.output_text_array)

                if hasattr(resp, "output"):
                    for item in resp.output:
                        if hasattr(item, "content"):
                            for c in item.content:
                                if hasattr(c, "text") and c.text:
                                    return c.text

                return str(resp)
            except Exception as e:
                return f"[OpenAI Parsing Error] {e}\nRaw Response: {str(resp)}"

        elif self.provider == "gemini":
            model = self.client.GenerativeModel(
                self.model,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "max_output_tokens": 2048,
                }
            )
            try:
                response = model.generate_content(
                    system_prompt + "\n\n" + user_prompt,
                    request_options={"timeout": 25}
                )
                return response.text
            except Exception as e:
                return f"[Gemini Error] {e}"

        else:
            raise ValueError(f"Unknown provider: {self.provider}")
