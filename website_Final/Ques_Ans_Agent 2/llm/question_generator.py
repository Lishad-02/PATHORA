# llm/question_generator.py

from typing import Dict, Any, List
from llm.llm_client import LLMClient
from llm.utils import extract_json_from_text
import random


# ======================================================
#  ENTRY-LEVEL + STRICT RULES + SAFETY-EXTENSION
# ======================================================
ENTRY_LEVEL_SYSTEM_PROMPT = """
You are a Question Generation Engine for evaluating ENTRY-LEVEL candidates or fresh graduates.

### STRICT RULES

1. QUESTIONS MUST BE ENTRY-LEVEL.
   - NO senior-level engineering topics.
   - NO multi-threading, concurrency, memory-mapping, ABI layout, strict-aliasing,
     compiler internals, DI disposal semantics, advanced SQL optimization,
     system redesigns, or architecture migration.

2. DIFFICULTY DEFINITIONS:
   - EASY → syntax, definitions, simple concepts.
   - MEDIUM → small real-world tasks (simple functions, simple JOINs, basic debugging).
   - HARD → only "entry-level hard":
       recursion basics, list reversal, window function ROW_NUMBER, 
       simple multi-step reasoning — but still beginner-friendly.

3. VALID STYLES:
   - coding: short coding tasks (≤ 10 lines expected).
   - concept: explain a fundamental idea.
   - debugging: find/fix a simple bug in a small snippet.
   - multiple_choice: 1 correct answer, 3 distractors.
     * For multiple_choice: you MUST generate A), B), C), and D) options.
       No missing options. Exactly 4 options.
       The correct answer must be explicitly included in expected_answer.

4. QUESTIONS MUST BE SHORT, CLEAR, AND CONCRETE.
   - No unnecessary storylines.
   - No multi-part giant questions.

5. Ensure topic diversity. Avoid repeating earlier question concepts.

6. ALWAYS RETURN STRICT JSON:
{
  "question": "...",
  "difficulty": "easy|medium|hard",
  "type": "concept|coding|debug|multiple_choice",
  "expected_answer": "...",
  "score_rubric": {
    "excellent": "...",
    "good": "...",
    "poor": "..."
  }
}

No extra words. No markdown. JSON only.


=========================================================
### 🔒 ADDITIONAL SAFETY & COMPLETENESS RULES
=========================================================

7. You MUST return EXACTLY ONE question.
   - Never generate multiple questions in one response.
   - Never provide alternatives or choices.

8. If the question references code:
   - You MUST include full runnable or logically complete code.
   - Code MUST be inside triple backticks ``` within the JSON field.
   - Debug questions must *always* contain a code snippet to fix.

9. JSON must ALWAYS contain all required fields:
   - question
   - difficulty
   - type
   - expected_answer
   - score_rubric {excellent, good, poor}

10. The question must NOT be vague or incomplete.
    - NEVER say “fix the above code” unless the full code is provided.
    - NEVER say “complete the missing part” unless the missing part is shown.

11. expected_answer MUST fully answer the generated question.

12. score_rubric MUST contain meaningful criteria.

13. ABSOLUTELY NO text outside the JSON.
=========================================================

Follow ALL rules strictly.
"""


# ======================================================
#  BLOCKED KEYWORDS TO PREVENT ADVANCED QUESTIONS
# ======================================================
BLOCKED_KEYWORDS = [
    "memory map", "mmap", "ABI", "concurrency", "race condition",
    "multi-thread", "thread safe", "strict aliasing",
    "binary format", "endianness", "on-disk", "serialization format",
    "dependency injection disposal", "service lifetime", "TLS", "atomic",
    "compiler optimization", "performance tuning", "index strategy"
]


class QuestionGenerator:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.used_questions = set()

    # --------------------------------------------------
    # JSON extraction helper
    # --------------------------------------------------
    def _try_generate(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        raw = self.llm.generate(system_prompt, user_prompt)
        if not raw or not isinstance(raw, str) or raw.strip() == "":
            return {}

        try:
            return extract_json_from_text(raw)
        except Exception:
            return {}

    # --------------------------------------------------
    # Duplicate Prevention
    # --------------------------------------------------
    def _is_duplicate(self, question_text: str) -> bool:
        return question_text.strip().lower() in self.used_questions

    def _mark_used(self, question_text: str):
        self.used_questions.add(question_text.strip().lower())

    # --------------------------------------------------
    # Validate topic safety
    # --------------------------------------------------
    def _is_blocked(self, text: str) -> bool:
        if not text:
            return False
        lower = text.lower()
        return any(k in lower for k in BLOCKED_KEYWORDS)

    # --------------------------------------------------
    # MAIN GENERATION LOGIC
    # --------------------------------------------------
    def generate_question(
        self,
        skill: str,
        skill_topics: List[str],
        difficulty: str,
        performance_hint: str,
    ) -> Dict[str, Any]:

        chosen_topic = random.choice(skill_topics) if skill_topics else skill
        q_style = random.choice(["coding", "concept", "debug", "multiple_choice"])

        user_prompt = f"""
Skill: "{skill}"
Subtopic to focus on: "{chosen_topic}"
Target difficulty: "{difficulty}"
Style: "{q_style}"
Previous performance: "{performance_hint}"

Generate ONE entry-level question.
It must follow all rules.
Return STRICT JSON only.
"""

        # FIRST ATTEMPT
        data = self._try_generate(ENTRY_LEVEL_SYSTEM_PROMPT, user_prompt)

        if (
            data
            and isinstance(data, dict)
            and data.get("question")
            and not self._is_duplicate(data["question"])
            and not self._is_blocked(data["question"])
        ):
            self._mark_used(data["question"])
            return data

        # SECOND ATTEMPT (simplified)
        retry_prompt = f"""
Generate ONE beginner-friendly {difficulty} {q_style} question for the skill "{skill}", focusing on topic "{chosen_topic}".
Return STRICT JSON ONLY.
"""

        data = self._try_generate(ENTRY_LEVEL_SYSTEM_PROMPT, retry_prompt)

        if (
            data
            and isinstance(data, dict)
            and data.get("question")
            and not self._is_duplicate(data["question"])
            and not self._is_blocked(data["question"])
        ):
            self._mark_used(data["question"])
            return data

        # ------------------------------------------------------
        # FINAL SAFE FALLBACK (Guaranteed valid JSON)
        # ------------------------------------------------------
        fallback_q = f"Explain the basic concept of '{chosen_topic}' in the context of {skill}."

        return {
            "question": fallback_q,
            "difficulty": difficulty,
            "type": "concept",
            "expected_answer": f"A simple beginner-friendly explanation of {chosen_topic} related to {skill}.",
            "score_rubric": {
                "excellent": "Clear explanation with a small example.",
                "good": "Mostly correct but missing some details.",
                "poor": "Incorrect or vague explanation."
            }
        }
