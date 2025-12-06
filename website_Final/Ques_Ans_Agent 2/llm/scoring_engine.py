# llm/scoring_engine.py

from typing import Dict, Any

from llm.llm_client import LLMClient
from llm.utils import extract_json_from_text


class ScoringEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _try_eval(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        raw = self.llm.generate(system_prompt, user_prompt)
        if not raw or not isinstance(raw, str) or raw.strip() == "":
            return {}
        try:
            return extract_json_from_text(raw)
        except Exception:
            return {}

    def _score_once(
        self,
        question: str,
        expected_answer: str,
        rubric: Dict[str, str],
        user_answer: str,
    ) -> Dict[str, Any]:

        system_prompt = (
            "You are an expert technical interviewer. "
            "You strictly evaluate answers using the given rubric and always return JSON."
        )

        user_prompt = f"""
Evaluate the candidate's answer.

Question:
{question}

Expected ideal answer:
{expected_answer}

User's answer:
{user_answer}

Rubric:
Excellent: {rubric.get("excellent", "")}
Good: {rubric.get("good", "")}
Poor: {rubric.get("poor", "")}

Instructions:
- Assign a score from 0 to 10.
- Provide short feedback (2–4 sentences).
- Decide ONLY ONCE if a follow-up question is required.
- If needed, ask ONE follow-up question.
- NEVER ask more than one follow-up question.

Return STRICT JSON:

{{
  "score": 0-10 number,
  "feedback": "short feedback",
  "need_followup": true or false,
  "followup_question": "text or empty string"
}}
"""
        data = self._try_eval(system_prompt, user_prompt)
        if data:
            return data

        return {
            "score": 5.0,
            "feedback": "Fallback scoring.",
            "need_followup": False,
            "followup_question": ""
        }

    # ---------------------------------------------------------
    # ONE follow-up MAX. NEVER generate multiple followups.
    # ---------------------------------------------------------
    def score_with_optional_followup(
        self,
        question: str,
        expected_answer: str,
        rubric: Dict[str, str],
        user_answer: str,
        max_followups: int = 1
    ) -> Dict[str, Any]:

        eval_first = self._score_once(question, expected_answer, rubric, user_answer)

        score = float(eval_first.get("score", 0.0))
        feedback = eval_first.get("feedback", "")
        need_followup = bool(eval_first.get("need_followup", False))
        followup_q = (eval_first.get("followup_question") or "").strip()

        if max_followups <= 0 or not need_followup or not followup_q:
            return {
                "final_score": score,
                "final_feedback": feedback,
                "followup_question": "",
                "followup_answer": "",
            }

        # Return exactly ONE follow-up
        return {
            "final_score": score,
            "final_feedback": feedback,
            "followup_question": followup_q,
            "followup_answer": "",
        }

    # ---------------------------------------------------------
    # FINAL followup evaluation (NO more follow-ups allowed)
    # ---------------------------------------------------------
    def apply_followup(
        self,
        question: str,
        expected_answer: str,
        rubric: Dict[str, str],
        main_answer: str,
        followup_answer: str,
    ) -> Dict[str, Any]:

        combined = (
            f"Main answer:\n{main_answer}\n\n"
            f"Follow-up answer:\n{followup_answer}"
        )

        # 🔥 CRITICAL: Disallow further followups
        system_prompt = (
            "You are an expert technical interviewer.\n"
            "Re-evaluate the candidate using BOTH answers.\n"
            "IMPORTANT RULES:\n"
            "- NEVER ask another follow-up.\n"
            "- NEVER output 'need_followup' or 'followup_question'.\n"
            "- NEVER suggest more clarifications.\n"
            "- Output STRICT JSON with EXACTLY TWO fields: score, feedback."
        )

        user_prompt = f"""
Re-evaluate using BOTH answers.

Question:
{question}

Expected ideal answer:
{expected_answer}

Combined answers:
{combined}

Rubric:
Excellent: {rubric.get('excellent','')}
Good: {rubric.get('good','')}
Poor: {rubric.get('poor','')}

STRICT JSON ONLY:

{{
  "score": 0-10 number,
  "feedback": "short feedback"
}}
"""

        result = self._try_eval(system_prompt, user_prompt)
        if result:
            return {
                "final_score": float(result.get("score", 0.0)),
                "final_feedback": result.get("feedback", "")
            }

        return {
            "final_score": 0.0,
            "final_feedback": "Fallback follow-up evaluation failure."
        }
