from skill_generator import generate_skills
import time

# =====================================
# USER INPUT / PREFERENCES
# =====================================

user_preferences = {
    "job_type": "",                     # SWE / Data Analyst
    "specific_role": "Full Stack Developer(Software Engineering)",  # frontend / backend / full stack
    "preparation_time": 12,                 # months
    "location": "Global",              # Global / Bangladesh
    "study_hours": 8,                     # daily hours
    "experience_level": "University recent CSE graduate",        # Beginner / Intermediate / Advanced
    "other_preferences": (
        "need fast job, Intermediate (Built small projects) coding experience, familiar with java, C,C++,javascript,typescript,php,kotlin Language and familiar with dot net,node.js,express.js,react framework. build some academic and personal projects & also done intership.preferable language is C# and javascript"
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
    
    # If you loop this script for multiple inputs later, this delay protects your quota
    time.sleep(12)