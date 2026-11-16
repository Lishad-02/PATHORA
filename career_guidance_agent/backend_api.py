from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json, os
import traceback
# === Agent modules ===
from agent.phase1 import run_phase1
from agent.phase1_5_refiner import refine_skills
from agent.refined_to_cleaned import simplify_refined_output
from agent.phase1_7_personalizer import personalize_skills
from agent.phase2_curriculum_builder import build_curriculum
from agent.phase2_learning_plan_prompt import generate_plan
from agent.phase2_verifier import verify_plan
from agent.phase2_time_calibrator import calibrate_time


app = FastAPI(title="AI Career Guidance Agent API")

# Allow frontend (HTML/JS) access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Step 1: Start session / greeting
# -----------------------------
@app.get("/start_session")
def start_session():
    message = (
        "👋 Hi, I’m your AI Career Guidance Agent!\n"
        "I can help you prepare for **Software Engineering** or **Data Analyst** jobs.\n"
        "Please choose one role to begin."
    )
    return JSONResponse(content={"message": message, "options": ["software_engineer", "data_analyst"]})


# -----------------------------
# Step 2: Generate Skill Recommendations
# -----------------------------
@app.post("/generate_skills")
async def generate_skills(request: Request):
    try:
        data = await request.json()
        job_role = data["job_role"]
        location = data["location"]
        persona = data["persona"]
        time_preference = data["time_preference"]
        preference = data.get("preference", "")
        provider = "gemini"
        print(f"\n🔍 Received from frontend => role: {job_role}, location: {location}, persona: {persona}, time: {time_preference}, pref: {preference}\n")
        os.makedirs("outputs", exist_ok=True)

        # === Phase 1: Skill recommendation pipeline ===
        result_gemini = run_phase1(
            location=location,
            persona=persona,
            time=time_preference,
            preference=preference,
            provider=provider,
            role=job_role,
        )


         # Save current Phase 1 output so next steps use the right persona data
        phase1_path = "outputs/phase1_output.json"
        with open(phase1_path, "w", encoding="utf-8") as f:
            json.dump(result_gemini, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved current phase1 output ({persona}) → {phase1_path}")

        # === Phase 1.5 & 1.6: Refinement and Cleaning ===
        refine_skills(
            input_file=phase1_path,
            time_preference=time_preference,
            model="gpt-5-mini",
            role=job_role,
        )

        simplify_refined_output(
            refined_path="outputs/phase1_5_refined.json",
            output_path="outputs/phase1_6_cleaned.json",
        )

        # === Load final cleaned skills ===
        with open("outputs/phase1_6_cleaned.json", "r", encoding="utf-8") as f:
            skills = json.load(f)

        print("✅ Simplified skill set saved to outputs/phase1_6_cleaned.json")
        return JSONResponse(content={"status": "success", "skills": skills}, media_type="application/json")

    except Exception as e:
          print("❌ ERROR during /generate_skills:")
          traceback.print_exc()  # print full traceback in console
          return JSONResponse(content={"error": str(e)}, status_code=500)


# -----------------------------
# Step 3: Personalization — remove known skills
# -----------------------------
@app.post("/remove_known_skills")
async def remove_known_skills(request: Request):
    try:
        data = await request.json()
        known_skills = data.get("known_skills", [])
        cleaned_file = "outputs/phase1_6_cleaned.json"

        updated = personalize_skills(cleaned_file, known_skills)

        return JSONResponse(
            content={
                "status": "updated",
                "known_skills": known_skills,
                "updated_skills": updated,
            },
            media_type="application/json",
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# -----------------------------
# Step 4: Generate Full Learning Plan
# -----------------------------
@app.post("/generate_learning_plan")
async def generate_learning_plan(request: Request):
    try:
        data = await request.json()
        job_role = data["job_role"]
        time_preference = data["time_preference"]
        daily_hours = float(data.get("daily_hours", 3))

        # === Run full curriculum pipeline ===
        build_curriculum("outputs/phase1_6_cleaned.json", job_role)
        generate_plan("outputs/phase2_1_curriculum.json", time_preference, daily_hours, job_role)
        verify_plan("outputs/phase2_learning_plan.json", job_role)
        calibrate_time(
            plan_file="outputs/phase2_learning_plan.json",
            verifier_file="outputs/phase2_verified.json",
            daily_hours=daily_hours,
            time_preference=time_preference,
            role=job_role,
        )

        # === Load outputs ===
        with open("outputs/phase2_learning_plan.json", "r", encoding="utf-8") as f:
            plan = json.load(f)
        with open("outputs/phase2_time_calibration.json", "r", encoding="utf-8") as f:
            calibration = json.load(f)

        return JSONResponse(
            content={
                "status": "complete",
                "learning_plan": plan,
                "calibration": calibration,
            },
            media_type="application/json",
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# -----------------------------
# Utility routes (optional)
# -----------------------------
@app.get("/get_skills")
def get_skills():
    try:
        with open("outputs/phase1_6_cleaned.json", "r", encoding="utf-8") as f:
            skills = json.load(f)
        return JSONResponse(content={"skills": skills})
    except FileNotFoundError:
        return JSONResponse(content={"error": "No skill data found yet."}, status_code=404)


@app.get("/get_learning_plan")
def get_learning_plan():
    try:
        with open("outputs/phase2_learning_plan.json", "r", encoding="utf-8") as f:
            plan = json.load(f)
        with open("outputs/phase2_time_calibration.json", "r", encoding="utf-8") as f:
            calibration = json.load(f)
        return JSONResponse(content={"plan": plan, "calibration": calibration})
    except FileNotFoundError:
        return JSONResponse(content={"error": "Learning plan not generated yet."}, status_code=404)


@app.get("/")
def root():
    return JSONResponse(content={"message": "Career Guidance Agent API is running 🚀"})
