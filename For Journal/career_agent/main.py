from skill_generator import generate_skills

# =====================================
# USER INPUT / PREFERENCES
# =====================================

user_preferences = {
    "job_type": "(Data Analyst/ Analytics / AI Engineer)",                     # SWE / Data Analyst
    "specific_role": "Machine Learning Engineer",  # frontend / backend / full stack
    "preparation_time": 8,                 # months
    "location": "Global",              # Global / Bangladesh
    "study_hours": 4,                     # daily hours
    "experience_level": "University Final Year CSE Student",        # Beginner / Intermediate / Advanced
    "other_preferences": (
        "Intermediate (Built small projects) coding experience, familiar with python, java, C, C++ Language and familiar with node.js,Express.js,Pytorch Framework. build some academic projects. prefer python languge and practical learning"
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
