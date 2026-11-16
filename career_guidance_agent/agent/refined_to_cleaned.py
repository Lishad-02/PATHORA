import json
import os

def simplify_refined_output(
    refined_path="../outputs/phase1_5_refined.json",
    output_path="../outputs/phase1_6_cleaned.json"
):
    """
    Simplifies the refined LLM output JSON:
    - Keeps only categories, skill name, and reasoning.
    - Removes 'kept_or_removed' and filters out removed skills.
    """

    # --- Check if refined file exists ---
    if not os.path.exists(refined_path):
        raise FileNotFoundError(f"❌ Refined JSON not found at: {os.path.abspath(refined_path)}")

    with open(refined_path, "r", encoding="utf-8") as f:
        refined = json.load(f)

    cleaned = {}

    for category, subcats in refined.items():
        if category in ["feasibility", "reasoning"]:
            continue

        cleaned[category] = {}
        for subcat, skills in subcats.items():
            kept = [
                {"name": s["name"], "reason": s["reason"]}
                for s in skills if s.get("kept_or_removed", "").lower() == "kept"
            ]
            cleaned[category][subcat] = kept

    # Ensure correct output folder path (one level up)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=4, ensure_ascii=False)

    print(f"✅ Simplified skill set saved to {os.path.abspath(output_path)}")
    return cleaned


if __name__ == "__main__":
    simplify_refined_output()
