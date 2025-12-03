# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os, json, datetime
from typing import Optional, List, Dict, Any

from backend.services.recommender import run_swe_recommendation

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(APP_ROOT, "data", "users")
os.makedirs(USER_DATA_DIR, exist_ok=True)

app = FastAPI(title="Career Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class LoginPayload(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class RecommendPayload(BaseModel):
    email: EmailStr
    job_category: str           # "SWE" | "DA"
    role: str                   # e.g., "Backend Developer"
    region: str                 # "Bangladesh" | "Global"
    duration_months: int        # user-chosen or from predefined
    preference: Optional[str] = ""  # free text

# ---------- Helpers ----------
def user_path(email: str) -> str:
    safe = email.replace("/", "_")
    return os.path.join(USER_DATA_DIR, f"{safe}.json")

def load_user(email: str) -> Dict[str, Any]:
    path = user_path(email)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user(email: str, data: Dict[str, Any]):
    path = user_path(email)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- Routes ----------
@app.post("/api/login")
def login(payload: LoginPayload):
    u = load_user(payload.email)
    if not u:
        u = {
            "email": payload.email,
            "name": payload.name or "",
            "profile": {},
            "recommended_skills": {},
            "completed_skills": [],
            "learning_path": {},
            "assessment_history": [],
            "chat_history": [],
            "last_session": None
        }
        save_user(payload.email, u)
    return {"ok": True, "user": u}

@app.get("/api/options")
def options(job_category: Optional[str] = None):
    # roles for SWE and DA (extend as needed)
    if job_category == "SWE":
        roles = ["Backend Developer", "Frontend Developer", "Full Stack", "DevOps", "Mobile Developer", "UI/UX Engineer"]
    elif job_category == "DA":
        roles = ["General Data Analyst", "Business Analyst", "Data Visualization Specialist", "ML Entry"]
    else:
        roles = []
    durations = [2,3,6,9,12]
    regions = ["Bangladesh", "Global"]
    return {"roles": roles, "durations": durations, "regions": regions}

@app.post("/api/recommend")
def recommend(payload: RecommendPayload):
    # Only SWE pipeline is implemented now (DA later)
    if payload.job_category not in ["SWE", "DA"]:
        raise HTTPException(status_code=400, detail="Invalid job category")
    if payload.job_category == "DA":
        raise HTTPException(status_code=501, detail="Data Analyst pipeline coming soon")

    # Map UI selections to your existing pipeline inputs
    location = payload.region                # "Bangladesh" | "Global"
    persona = _map_role_to_persona(payload.role)   # e.g., "Backend" for Backend Developer
    time_preference = f"{payload.duration_months} months"
    preference = payload.preference or ""

    # Run your existing pipeline
    cleaned = run_swe_recommendation(
        location=location,
        persona=persona,
        time_preference=time_preference,
        preference=preference,
        provider="gemini"
    )

    # Persist to user memory
    u = load_user(payload.email) or {"email": payload.email}
    u.setdefault("profile", {})
    u["profile"].update({
        "job_category": payload.job_category,
        "role": payload.role,
        "region": payload.region,
        "duration_months": payload.duration_months,
        "preference": payload.preference or ""
    })
    u["recommended_skills"] = cleaned
    u["last_session"] = datetime.datetime.utcnow().isoformat() + "Z"
    save_user(payload.email, u)

    return {"ok": True, "recommended_skills": cleaned, "user": u}

def _map_role_to_persona(role: str) -> str:
    role = role.lower()
    if "backend" in role: return "Backend"
    if "frontend" in role: return "Frontend"
    if "full" in role: return "Full Stack"
    if "devops" in role: return "DevOps"
    if "mobile" in role: return "Mobile"
    if "ui/ux" in role or "ui" in role or "ux" in role: return "UI/UX"
    # default to Backend if unknown
    return "Backend"
