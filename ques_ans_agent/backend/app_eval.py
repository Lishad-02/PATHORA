# backend/app_eval.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, Any
import uuid

from dotenv import load_dotenv
load_dotenv()

from core.difficulty_manager import DifficultyManager
from core.session_manager import SessionManager
from core.models import QuestionRecord

from llm.llm_client import LLMClient
from llm.dynamic_skill_mapper import DynamicSkillMapper
from llm.question_generator import QuestionGenerator
from llm.scoring_engine import ScoringEngine


# ------------------------------------------------------
# FASTAPI APP + CORS
# ------------------------------------------------------
app = FastAPI(title="Adaptive Evaluation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

QUESTION_PROVIDER = "openai"
QUESTION_MODEL = "gpt-5-mini"

SCORING_PROVIDER = "openai"
SCORING_MODEL = "gpt-5-mini"

SESSION_QUESTION_COUNT = 5


# -------------------------
# Request Models
# -------------------------
class StartEvaluationRequest(BaseModel):
    user_id: str
    skill: str


class SubmitAnswerRequest(BaseModel):
    session_id: str
    user_answer: str


class SubmitFollowupRequest(BaseModel):
    session_id: str
    followup_answer: str


# ------------------------------------------------------
# Evaluation Session Logic
# ------------------------------------------------------
class EvalSession:

    def __init__(self, user_id: str, skill: str, question_count: int = SESSION_QUESTION_COUNT):
        self.user_id = user_id
        self.skill = skill
        self.question_count = question_count
        self.current_index = 0

        self.performance_hint = "Start with medium difficulty."

        # LLM clients
        self.question_llm = LLMClient(provider=QUESTION_PROVIDER, model=QUESTION_MODEL)
        self.scoring_llm = LLMClient(provider=SCORING_PROVIDER, model=SCORING_MODEL)

        # Skill topics
        mapper = DynamicSkillMapper(self.question_llm)
        self.skill_topics = mapper.map_skill(skill)

        # Engines
        self.generator = QuestionGenerator(self.question_llm)
        self.generator.used_questions.clear()

        self.scorer = ScoringEngine(self.scoring_llm)
        self.difficulty_mgr = DifficultyManager(start_level="medium")

        # Session manager
        self.session_mgr = SessionManager(
            user_id=user_id,
            skill=skill,
            question_count=question_count,
        )

        # State for current question
        self.last_question_data: Optional[Dict[str, Any]] = None
        self.first_score_payload: Optional[Dict[str, Any]] = None
        self.first_main_answer: str = ""   # store user's main answer


    # ------------------------------------------------------
    # Generate NEXT question (always with index)
    # ------------------------------------------------------
    def get_next_question(self):
        if self.current_index >= self.question_count:
            return None

        difficulty = self.difficulty_mgr.current_level

        q_raw = self.generator.generate_question(
            skill=self.skill,
            skill_topics=self.skill_topics,
            difficulty=difficulty,
            performance_hint=self.performance_hint,
        )

        self.current_index += 1

    
        # Build full question dict including index
        q = {
            "index": self.current_index,
            "skill": self.skill,
            "difficulty": q_raw["difficulty"],
            "type": q_raw["type"],
            "question": q_raw["question"],
            "code_snippet": q_raw.get("code_snippet", ""),
            "options": q_raw.get("options", []),
            "expected_answer": q_raw["expected_answer"],
            "score_rubric": q_raw["score_rubric"],
        }

        self.last_question_data = q
        return q


    # ------------------------------------------------------
    # Step 1 – Process MAIN answer
    #  - If no follow-up: save record + adjust difficulty here
    #  - If follow-up: just return follow-up; final save happens in process_followup
    # ------------------------------------------------------
    def process_answer(self, user_answer: str) -> Dict[str, Any]:
        if not self.last_question_data:
            raise RuntimeError("No active question to score.")

        q = self.last_question_data

        self.first_main_answer = user_answer

        eval_result = self.scorer.score_with_optional_followup(
            question=q["question"],
            expected_answer=q["expected_answer"],
            rubric=q["score_rubric"],
            user_answer=user_answer,
            
            # Code snippet and options from the question
            code_snippet=q.get("code_snippet", ""), 
            options=q.get("options", []),
            
            max_followups=1,
        )

        self.first_score_payload = eval_result

        followup_q = (eval_result.get("followup_question") or "").strip()

        # ---- CASE A: no follow-up needed → finalize this question now ----
        if not followup_q:
            final_score = float(eval_result.get("final_score", 0.0))
            final_feedback = eval_result.get("final_feedback", "")

            # Adjust difficulty for next question
            new_level = self.difficulty_mgr.adjust(final_score)
            self.performance_hint = (
                f"Prev score {final_score:.1f}, next difficulty '{new_level}'."
            )

            # Save record for this question
            record = QuestionRecord(
                index=q["index"],
                skill=self.skill,
                difficulty=q["difficulty"],
                question=q["question"],
                expected_answer=q["expected_answer"],
                user_answer=self.first_main_answer,
                followup_question="",
                followup_answer="",
                score=final_score,
                feedback=final_feedback,
            )
            self.session_mgr.add_record(record, q["difficulty"])

            # Return like normal (no follow-up)
            return {
                "final_score": final_score,
                "final_feedback": final_feedback,
                "followup_question": "",
                "followup_answer": "",
            }

        # ---- CASE B: follow-up requested → frontend will call /submit-followup ----
        return eval_result


    # ------------------------------------------------------
    # Step 2 – Process FOLLOW-UP answer (only once)
    # ------------------------------------------------------
    def process_followup(self, followup_answer: str):
        if not self.last_question_data:
            raise RuntimeError("No question for follow-up.")
        if not self.first_score_payload:
            raise RuntimeError("No main scoring context for follow-up.")

        q = self.last_question_data

        # Re-evaluate using both main and follow-up answers
        reeval = self.scorer.apply_followup(
            question=q["question"],
            expected_answer=q["expected_answer"],
            rubric=q["score_rubric"],
            main_answer=self.first_main_answer,
            followup_answer=followup_answer,
        )

        final_score = float(reeval["final_score"])
        final_feedback = reeval["final_feedback"]

        # Adjust difficulty for next question
        new_level = self.difficulty_mgr.adjust(final_score)
        self.performance_hint = (
            f"Prev score {final_score:.1f}, next difficulty '{new_level}'."
        )

        # Save record including follow-up
        record = QuestionRecord(
            index=q["index"],
            skill=self.skill,
            difficulty=q["difficulty"],
            question=q["question"],
            expected_answer=q["expected_answer"],
            user_answer=self.first_main_answer,
            followup_question=self.first_score_payload.get("followup_question", ""),
            followup_answer=followup_answer,
            score=final_score,
            feedback=final_feedback,
        )
        self.session_mgr.add_record(record, q["difficulty"])

        return final_score, final_feedback


    # ------------------------------------------------------
    # Finalize session
    # ------------------------------------------------------
    def finalize(self):
        session = self.session_mgr.finalize()
        path = self.session_mgr.save_to_json(session)
        
        # Build a history list for the frontend report
        history = []
        
        for r in session.questions: 
            history.append({
                "index": r.index,
                "difficulty": r.difficulty,
                "score": r.score,
                "question": r.question,
                "feedback": r.feedback
            })
            
        return {
            "user_id": self.user_id,
            "skill": self.skill,
            "average_score": session.average_score,
            "difficulty_trajectory": session.difficulty_trajectory,
            "json_path": path,
            "history": history
        }


# ------------------------------------------------------
# In-memory sessions
# ------------------------------------------------------
SESSIONS: Dict[str, EvalSession] = {}


# ------------------------------------------------------
# API: start-evaluation
# ------------------------------------------------------
@app.post("/start-evaluation")
def start(req: StartEvaluationRequest):
    session_id = uuid.uuid4().hex
    sess = EvalSession(req.user_id, req.skill)
    SESSIONS[session_id] = sess

    first_q = sess.get_next_question()

    return {
        "session_id": session_id,
        "user_id": req.user_id,
        "skill": req.skill,
        "subtopics": sess.skill_topics,
        "question": first_q,
    }


# ------------------------------------------------------
# API: submit-answer (main answer)
# ------------------------------------------------------
@app.post("/submit-answer")
def submit(req: SubmitAnswerRequest):
    if req.session_id not in SESSIONS:
        raise HTTPException(404, "Session not found")

    sess = SESSIONS[req.session_id]
    res = sess.process_answer(req.user_answer)

    # If follow-up needed → stop here, let frontend call /submit-followup
    if res.get("followup_question"):
        return {
            "need_followup": True,
            "score": res["final_score"],
            "feedback": res["final_feedback"],
            "followup_question": res["followup_question"],
            "completed": False,
            "next_question": None,
        }

    # No follow-up → go to next question
    next_q = sess.get_next_question()
    done = next_q is None
    summary = sess.finalize() if done else None

    return {
        "need_followup": False,
        "score": res["final_score"],
        "feedback": res["final_feedback"],
        "followup_question": "",
        "completed": done,
        "next_question": next_q,
        "summary": summary,
    }


# ------------------------------------------------------
# API: submit-followup
# ------------------------------------------------------
@app.post("/submit-followup")
def submit_followup(req: SubmitFollowupRequest):
    if req.session_id not in SESSIONS:
        raise HTTPException(404, "Session not found")

    sess = SESSIONS[req.session_id]
    score, feedback = sess.process_followup(req.followup_answer)

    next_q = sess.get_next_question()
    done = next_q is None
    summary = sess.finalize() if done else None

    return {
        "completed": done,
        "score": score,
        "feedback": feedback,
        "next_question": next_q,
        "summary": summary,
    }
