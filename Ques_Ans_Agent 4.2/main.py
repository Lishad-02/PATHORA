# main.py

from dotenv import load_dotenv
load_dotenv()

from core.difficulty_manager import DifficultyManager
from core.session_manager import SessionManager
from core.models import QuestionRecord

from llm.llm_client import LLMClient
from llm.dynamic_skill_mapper import DynamicSkillMapper
from llm.question_generator import QuestionGenerator
from llm.scoring_engine import ScoringEngine


# CONFIG
# QUESTION_PROVIDER = "gemini"
# QUESTION_MODEL = "gemini-2.5-flash"

QUESTION_PROVIDER = "openai"
QUESTION_MODEL = "gpt-5-mini"

SCORING_PROVIDER = "openai"
SCORING_MODEL = "gpt-5-mini"   # change if your model name is different

SESSION_QUESTION_COUNT = 4


def get_multiline_input(prompt: str) -> str:
    print(prompt)
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def run_adaptive_evaluation():
    

    print("=== Adaptive Skill Evaluation (Terminal Version) ===")

    user_id = input("Enter user id / email: ").strip()
    skill = input("Enter skill to evaluate (e.g., 'Python', 'SQL', 'Prompt Engineering'): ").strip()

    # Initialize LLM clients
    question_llm = LLMClient(provider=QUESTION_PROVIDER, model=QUESTION_MODEL)
    scoring_llm = LLMClient(provider=SCORING_PROVIDER, model=SCORING_MODEL)

    # Skill mapping (dynamic topics)
    mapper = DynamicSkillMapper(question_llm)
    skill_topics = mapper.map_skill(skill)

    print("\nIdentified subtopics for this skill:")
    for t in skill_topics:
        print(" -", t)

    generator = QuestionGenerator(question_llm)

    # IMPORTANT: ensure we start fresh in every session
    generator.used_questions.clear()
    scorer = ScoringEngine(scoring_llm)
    difficulty_mgr = DifficultyManager(start_level="medium")
    session_mgr = SessionManager(
        user_id=user_id,
        skill=skill,
        question_count=SESSION_QUESTION_COUNT,
    )

    performance_hint = "Start with a balanced medium difficulty question."

    for i in range(1, SESSION_QUESTION_COUNT + 1):
        print(f"\n--- Question {i} of {SESSION_QUESTION_COUNT} ---")

        difficulty = difficulty_mgr.current_level

        # Generate question
        q_data = generator.generate_question(
            skill=skill,
            skill_topics=skill_topics,
            difficulty=difficulty,
            performance_hint=performance_hint,
        )

        question_text = q_data.get("question", "").strip()
        difficulty_from_model = q_data.get("difficulty", difficulty)
        q_type = q_data.get("type", "short_answer")
        expected_answer = q_data.get("expected_answer", "").strip()
        rubric = q_data.get("score_rubric", {})

        print(f"\n[{difficulty_from_model.upper()}] ({q_type})")
        print("Question:", question_text)

        user_answer = get_multiline_input(
            "\nEnter your answer (finish by typing a single line with 'END'):"
        )

        # Score + possible follow-up
        eval_result = scorer.score_with_optional_followup(
            question=question_text,
            expected_answer=expected_answer,
            rubric=rubric,
            user_answer=user_answer,
        )

        score = eval_result["final_score"]
        feedback = eval_result["final_feedback"]
        followup_q = eval_result["followup_question"]
        followup_a = eval_result["followup_answer"]

        print(f"\n✅ Score for this question: {score:.1f} / 10")
        print("💬 Feedback:", feedback)

        # Adjust difficulty for next question
        new_level = difficulty_mgr.adjust(score)
        performance_hint = (
            f"Previous score: {score:.1f}/10. Next question should be around '{new_level}' difficulty."
        )

        # Store record
        record = QuestionRecord(
            index=i,
            skill=skill,
            difficulty=difficulty_from_model,
            question=question_text,
            expected_answer=expected_answer,
            user_answer=user_answer,
            followup_question=followup_q,
            followup_answer=followup_a,
            score=score,
            feedback=feedback,
        )
        session_mgr.add_record(record, difficulty_from_model)

    # Finalize and save
    session = session_mgr.finalize()
    path = session_mgr.save_to_json(session)

    print("\n=== Session Complete ===")
    print(f"Average score: {session.average_score:.2f} / 10")
    print("Difficulty trajectory:", " → ".join(session.difficulty_trajectory))
    print(f"Session saved to: {path}")


if __name__ == "__main__":
    run_adaptive_evaluation()
