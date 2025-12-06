# from .llm_openai import call_openai   # disable this for now
from .llm_gemini import call_gemini

def call_llm(prompt, provider="gemini", **kwargs):
    # if provider == "openai":
    #     return call_openai(prompt, **kwargs)
    if provider == "gemini":
        return call_gemini(prompt, **kwargs)
    else:
        raise ValueError("Unknown LLM provider")
