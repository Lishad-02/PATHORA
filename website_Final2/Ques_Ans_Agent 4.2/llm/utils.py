# llm/utils.py

import json
from typing import Any, Dict


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Try to extract the first JSON object from a larger text.
    Handles cases where the model wraps JSON in markdown or explanations.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Empty or non-string text for JSON extraction.")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not find JSON object in text: {text}")
    json_str = text[start:end + 1]
    return json.loads(json_str)
