# backend/services/recommender.py
import json
import os
from agent.phase1 import run_phase1
from agent.phase1_5_refiner import refine_skills
from agent.refined_to_cleaned import simplify_refined_output

OUTPUT_DIR = "outputs"
PHASE1_PATH = os.path.join(OUTPUT_DIR, "phase1_output.json")
PHASE15_PATH = os.path.join(OUTPUT_DIR, "phase1_5_refined.json")
PHASE16_PATH = os.path.join(OUTPUT_DIR, "phase1_6_cleaned.json")

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_swe_recommendation(location: str, persona: str, time_preference: str, preference: str, provider: str = "gemini"):
    """
    Runs your existing pipeline:
      Phase 1  -> run_phase1(...)
      Phase 1.5-> refine_skills(...)
      Phase 1.6-> simplify_refined_output(...)
    Returns the cleaned (Phase 1.6) JSON as a Python dict.
    """
    ensure_dirs()

    # === PHASE 1 ===
    result_gemini = run_phase1(
        location=location,
        persona=persona,     # e.g., "Backend" / "Frontend"
        time=time_preference,  # e.g., "3 months"
        preference=preference,
        provider=provider
    )
    with open(PHASE1_PATH, "w", encoding="utf-8") as f:
        json.dump(result_gemini, f, indent=4, ensure_ascii=False)

    # === PHASE 1.5 ===
    refined_result = refine_skills(
        input_file=PHASE1_PATH,
        time_preference=time_preference,
        model="gpt-5-mini"
    )
    with open(PHASE15_PATH, "w", encoding="utf-8") as f:
        json.dump(refined_result, f, indent=4, ensure_ascii=False)

    # === PHASE 1.6 ===
    cleaned_result = simplify_refined_output(
        refined_path=PHASE15_PATH,
        output_path=PHASE16_PATH
    )

    # Return cleaned_result dict (already saved by simplify_refined_output)
    return cleaned_result
