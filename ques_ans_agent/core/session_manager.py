# core/session_manager.py

import os
import json
import datetime
from dataclasses import asdict
from typing import List

from core.models import QuestionRecord, EvaluationSession


class SessionManager:
    def __init__(self, user_id: str, skill: str, question_count: int):
        self.user_id = user_id
        self.skill = skill
        self.question_count = question_count
        self.records: List[QuestionRecord] = []
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"{user_id}_{skill}_{now}"
        self.difficulty_trajectory: List[str] = []

    def add_record(self, record: QuestionRecord, difficulty: str):
        self.records.append(record)
        self.difficulty_trajectory.append(difficulty)

    def finalize(self) -> EvaluationSession:
        avg_score = (
            sum(r.score for r in self.records) / len(self.records)
            if self.records
            else 0.0
        )
        created_at = datetime.datetime.now().isoformat()
        session = EvaluationSession(
            session_id=self.session_id,
            user_id=self.user_id,
            skill=self.skill,
            created_at=created_at,
            questions=self.records,
            average_score=avg_score,
            difficulty_trajectory=self.difficulty_trajectory,
        )
        return session

    def save_to_json(self, session: EvaluationSession, output_dir: str = "evaluations") -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{session.session_id}.json")
        data = asdict(session)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
