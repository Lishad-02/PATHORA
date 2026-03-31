from skill_generator import generate_skills

# =====================================
# USER INPUT / PREFERENCES
# =====================================

user_preferences = {
    "job_type": "(Data Analyst/ Analytics / AI Engineer)",                     # SWE / Data Analyst
    "specific_role": "Data Scientist",  # frontend / backend / full stack
    "preparation_time": 6,                 # months
    "location": "Global",              # Global / Bangladesh
    "study_hours": 2,                     # daily hours
    "experience_level": "University Recent CSE Graduate",        # Beginner / Intermediate / Advanced
    "other_preferences": (
        " Love innovtive work, Advanced (Internship / Real-world experience) coding experience, familiar with python, java, C Language and familiar with django,Flask,React,Tensorflow,Pytorch Framework. build some academic, personal and real-world projects.Preferable language is Python."
    )
}

# =====================================
# PIPELINE EXECUTION (STEP 1 ONLY)
# =====================================

if __name__ == "__main__":
    print("🚀 Running Step 1: Skill Generation...\n")

    output = generate_skills(user_preferences)

    print("✅ Step 1 completed successfully.")
    print("📄 Output saved to outputs/step1_generated_skills.json")
