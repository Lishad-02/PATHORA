# core/models.py

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class QuestionRecord:
    index: int
    skill: str
    difficulty: str
    question: str
    expected_answer: str
    user_answer: str
    followup_question: Optional[str]
    followup_answer: Optional[str]
    score: float
    feedback: str


@dataclass
class EvaluationSession:
    session_id: str
    user_id: str
    skill: str
    created_at: str
    questions: List[QuestionRecord]
    average_score: float
    difficulty_trajectory: List[str]
