from agent.phase1 import run_phase1
from agent.phase1_5_refiner import refine_skills
from agent.refined_to_cleaned import simplify_refined_output
from agent.phase2_time_calibrator import calibrate_time
import json
import os




# phase 1 and 1.5 code is here

if __name__ == "__main__":
    print("\n===== Agent (Gemini Skill Recommender) =====")

    # === USER INPUT ===
    job_role = "Data Analyst"   
    location = "Global"
    persona = "" if job_role == "software_engineer" else "Data Analyst"
    time_preference = "8 months"
    preference ="do not give python"
    provider = "gemini"

    print(f"\n🎯 Running career guidance for role: {job_role.upper()} in {location}")

    # === PHASE 1: Skill Recommendation ===
    result_gemini = run_phase1(
        location=location,
        persona=persona,
        time=time_preference,
        preference=preference,
        provider=provider,
        role=job_role
    )


    # Pretty print Phase 1 output
    print(json.dumps(result_gemini, indent=4, ensure_ascii=False))

    # Create outputs directory
    os.makedirs("outputs", exist_ok=True)

    # Save Phase 1 output (static filename)
    phase1_filename = "outputs/phase1_output.json"
    with open(phase1_filename, "w", encoding="utf-8") as f:
        json.dump(result_gemini, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Phase 1 output saved to {phase1_filename}")

    # === PHASE 1.5: Time Feasibility Refinement ===
    print("\n===== OpenAI Refiner (Time Feasibility Adjustment) =====")
    refined_result = refine_skills(
     input_file=phase1_filename,
     time_preference=time_preference,
     model="gpt-5-mini",
     role=job_role
    )

    # Pretty print refined output
    print(json.dumps(refined_result, indent=4, ensure_ascii=False))

    # Save refined version (static filename)
    refined_filename = "outputs/phase1_5_refined.json"
    with open(refined_filename, "w", encoding="utf-8") as f:
        json.dump(refined_result, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Refined (time-feasible) output saved to {refined_filename}")



# Learning Plan Generation and Verification
# Learning Plan Generation and Verification
# Learning Plan Generation and Verification

        # === PHASE 1.6: Simplified Cleaned Output ===
    print("\n===== Simplifying Output for Learning Plan (Phase 1.6) =====")
    try:
        cleaned_result = simplify_refined_output(
            refined_path="outputs/phase1_5_refined.json",
            output_path="outputs/phase1_6_cleaned.json"
        )

        print(json.dumps(cleaned_result, indent=4, ensure_ascii=False))
        print("\n✅ Simplified (Phase 1.6) output saved successfully!")

    except Exception as e:
        print(f"❌ Error while simplifying refined output: {e}")



        # === PERSONALIZATION STEP ===
        # === PHASE 1.7: Personalization via LLM ===
    print("\n===== Personalization Step (Phase 1.7): Remove Already-Known Skills =====")

    # Load list of all skills to display
    with open("outputs/phase1_6_cleaned.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    def extract_skill_names(obj):
        names = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                names += extract_skill_names(v)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and "name" in item:
                    names.append(item["name"])
        return names

    all_skills = extract_skill_names(data)
    print("\nYour current recommended skills are:\n")
    for s in all_skills:
        print(f" - {s}")

    known = input("\nEnter any skills you already know (comma-separated, or press Enter to skip): ").strip()
    if known:
        known_list = [k.strip() for k in known.split(",") if k.strip()]
        from agent.phase1_7_personalizer import personalize_skills
        personalize_skills("outputs/phase1_6_cleaned.json", known_list)
    else:
        print("No known skills entered. Keeping all recommendations.")















    # === PHASE 2.1: Curriculum Structuring (Gemini) ===
    print("\n===== Building Curriculum (Phase 2.1) =====")
    from agent.phase2_curriculum_builder import build_curriculum
    curriculum_result = build_curriculum("outputs/phase1_6_cleaned.json", job_role)

    # === PHASE 2.2: Time-Aware Learning Plan (GPT-5 Mini) ===
    print("\n===== Generating Learning Plan (Phase 2.2) =====")
    daily_hours = float(input("Enter average daily study hours: ") or 3)
    from agent.phase2_learning_plan_prompt import generate_plan
    plan_result = generate_plan("outputs/phase2_1_curriculum.json",
                                time_preference,
                                daily_hours,
                                job_role)

    # === PHASE 2.3: Plan Verification (Gemini) ===
    print("\n===== Verifying Plan Feasibility (Phase 2.3) =====")
    from agent.phase2_verifier import verify_plan
    verification = verify_plan("outputs/phase2_learning_plan.json", job_role)
    print(verification)


   #----------------------------------------------
   #---Time & Effort Calibration (Phase 2.4)---

from agent.phase2_time_calibrator import calibrate_time

print("\n===== Time & Effort Calibration (Phase 2.4) =====")
daily_hours_input = input("Enter your average daily study hours again for calibration: ")

calibration_result = calibrate_time(
    plan_file="outputs/phase2_learning_plan.json",
    verifier_file="outputs/phase2_verified.json",
    daily_hours=daily_hours_input,
    time_preference=time_preference,
    role=job_role
)
print("\n✅ Personalized calibration completed.\n", calibration_result)

