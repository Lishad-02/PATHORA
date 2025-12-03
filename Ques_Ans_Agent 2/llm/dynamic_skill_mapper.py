# llm/dynamic_skill_mapper.py

from typing import List

from llm.llm_client import LLMClient
from llm.utils import extract_json_from_text


class DynamicSkillMapper:
    """
    Breaks down ANY skill name (e.g., 'Python', 'Docker', 'TensorFlow', 'Prompt Engineering')
    into a list of subtopics to guide question generation.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def map_skill(self, skill: str) -> List[str]:
        system_prompt = "You are an expert technical interviewer and curriculum designer."
        user_prompt = f"""
The candidate wants to be evaluated on the skill: "{skill}".

Break this skill into 5-7 key subtopics that are typically assessed
in technical interviews for Software Engineering / Data Analyst roles.
Keep them short phrases, not full sentences.

Return STRICT JSON only, no explanation:

{{
  "skill_map": ["topic1", "topic2", "topic3"]
}}
"""
        raw = self.llm.generate(system_prompt, user_prompt)

        try:
            data = extract_json_from_text(raw)
            skill_map = data.get("skill_map", [])
            topics = [str(t).strip() for t in skill_map if isinstance(t, str) and t.strip()]
            if topics:
                return topics
        except Exception:
            pass

        # Fallback if parsing fails
        return [f"Core concepts of {skill}", f"Practical usage of {skill}"]
