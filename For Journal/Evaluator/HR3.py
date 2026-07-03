import json
import os
import time
from datetime import datetime
from openai import OpenAI



client         = OpenAI(api_key="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")
MODEL          = "gpt-4o-2024-08-06"
TEMPERATURE    = 0.0
PROMPT_VERSION = "v3.0-unbiased"

# ============================================================
# DIMENSION MAXIMUMS
# TCF subcriteria renamed to match unbiased outcome-focused prompt
# ============================================================

DIMENSION_MAXES = {
    "HRO": {
        "max": 25,
        "breakdown": {
            "core_technical": 8,
            "interview_prep": 8,
            "portfolio":      9
        }
    },
    "TCF": {
        "max": 15,
        "breakdown": {
            "feasibility":     5,
            "cognitive_load":  5,
            "appropriateness": 5
        }
    },
    "PPA": {
        "max": 15,
        "breakdown": {
            "experience_adaptation":  5,
            "preference_integration": 5,
            "stack_relevance":        5
        }
    },
    "MA": {
        "max": 10,
        "breakdown": {
            "skill_demand":     5,
            "global_alignment": 5
        }
    },
    "SPQ": {
        "max": 10,
        "breakdown": {
            "high_roi":    5,
            "progression": 5
        }
    },
    "CSDC": {
        "max": 15,
        "breakdown": {
            "knowledge_progression": 5,
            "content_specificity":   5,
            "actionability":         5
        }
    },
    "CER": {
        "max": 10,
        "breakdown": {
            "resume":               4,
            "mock_interviews":      3,
            "application_strategy": 3
        }
    }
}

# ============================================================
# USER PREFERENCES
# ============================================================

user_preferences = {
    "role": "Cybersecurity Engineer(Software Engineering)",  # frontend / backend / full stack
    "experience": "University Final Year CSE Student",
    "preparation_time_months": 6,
    "study_hours_per_day": 4,
    "Market_Focus": "Global",
    "other_preferences": (
        " little bit weak in programming, Intermediate (Built small projects) coding experience, familiar with Python, C and Java and familiar with django framework. Also build some academic project, preferable language is Python"
    )
}

role = user_preferences["role"]

# ============================================================
# SYSTEM MESSAGE
# ============================================================

SYSTEM_MESSAGE = (
    "You are a strict AI Curriculum Evaluator. "
    "Evaluate plans based on the SUBSTANCE and OUTCOMES they provide, "
    "not their formatting style or structural presentation. "
    "A plan in bullet points can score as high as a structured plan "
    "if the content quality is equivalent. "
    "Apply penalty flags only when components are entirely absent. "
    "Follow the rubric anchors exactly as written. "
    "Output only valid JSON matching the required format exactly."
)

# ============================================================
# EVALUATION PROMPT — OUTCOME-FOCUSED, UNBIASED
# ============================================================

EVALUATION_PROMPT = """
You are an independent expert evaluator assessing the quality of
AI-generated career learning plans.

Your evaluation must be OUTCOME-FOCUSED, not FORMAT-FOCUSED.
A plan expressed as bullet points can score as highly as a plan
expressed as structured JSON, provided the CONTENT and QUALITY
of guidance is equivalent.

Do NOT reward a plan simply because it:

Uses structured formatting, headers, or JSON-like presentation
Explicitly states numbers such as hours or weeks
Uses professional terminology or labels
Is longer or more verbose than another plan

DO reward a plan because it:

Genuinely prepares the user for the target role
Is realistically achievable given the user's constraints
Reflects the user's actual background and preferences
Contains actionable, specific guidance
Aligns with real job market demands

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 0 — TARGET ROLE CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Target Role: {role}

Evaluation MUST be performed relative to the skills, tools,
interview expectations, and portfolio standards of this role.

Do NOT assume AI/ML-specific requirements unless explicitly relevant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — FUNDAMENTAL SCORING RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOTTOM-UP SCORING (mandatory):
Step 1 → Score each subcriterion individually first.
Step 2 → Sum subcriteria to get the dimension total.
Step 3 → Sum all dimensions to get Total_Score.
Never decide the total first and reverse-engineer breakdowns.
Score the SUBSTANCE of guidance, not its presentation style.
If a plan achieves an outcome implicitly rather than explicitly,
award partial credit proportional to how well it is achieved.
Apply penalty deductions ONLY when a component is ENTIRELY
ABSENT from the plan. Partial presence = partial credit, NOT a penalty.
Breakdown scores MUST sum exactly to the dimension score.
No subcriterion may exceed its stated maximum.
Do NOT inflate scores. If uncertain, score lower.
Return ONLY valid JSON. No text or explanation outside the JSON.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2 — USER PROFILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{user_preferences}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — CALIBRATION ANCHORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

88-100 (Exceptional):
A plan at this level would make a hiring manager genuinely confident
the candidate followed it. It covers the right technical skills at
the right depth for the {role}. It includes meaningful, specific
projects relevant to the role. It prepares the user for actual
interviews with concrete practice mechanisms. It gives the user a
real job search strategy. The scope is achievable within the given
time constraints for the user's background.

74-87 (Good):
Solid plan that covers most necessary ground. A student following
it would be substantially more hireable. May have gaps in one or
two areas such as interview prep being light or project scope being
unclear, but the core technical content and timeline are sound.

58-73 (Average):
Covers the right general topics but lacks specificity or depth in
application. A student could follow it but would need to fill
significant gaps independently. Missing at least one major component
such as projects, interview prep, or job search guidance.

40-57 (Weak):
Identifies relevant skills but provides little actionable guidance.
A student following this would know WHAT to learn but not HOW,
in what order, or by when. Missing multiple major components.

Below 40 (Poor):
Does not meaningfully address the user profile or goal.

CRITICAL CALIBRATION NOTE:
If one plan is clearly more actionable, specific, and complete than
another, their Total_Scores MUST differ by at least 10-15 points.
Do NOT cluster both plans in the same 5-point range if they differ
meaningfully in quality. Discriminate clearly based on substance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4 — MISSING COMPONENT PENALTIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply ONLY when a component is ENTIRELY ABSENT.
Partial presence earns partial credit, not a penalty.
Document every applied penalty in the penalties_applied field.

P1: No time or scope guidance of any kind
→ Deduct 4 from TCF: feasibility capped at 1

P2: No interview preparation content of any kind
→ Deduct 5 from HRO: interview_prep capped at 3

P3: No project or applied work of any kind
→ Deduct 5 from HRO: portfolio capped at 4

P4: No connection to the user's specific background
→ Deduct 4 from PPA: experience_adaptation capped at 1

P5: No career execution content of any kind
→ Deduct 5 from CER: all subcriteria capped at 1 each

P6: Scope is clearly impossible for the stated timeline
→ Deduct 4 from TCF: cognitive_load capped at 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — SCORING MATRIX (GENERALIZED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

D1: HRO — Hiring Readiness Optimization (Max 25)

1a. core_technical (0-8)
QUESTION:
If this user follows this plan completely, will they have the
technical skills required to pass interviews for the {role}?

→ Evaluate based on role-relevant technologies and depth.

1b. interview_prep (0-8)
QUESTION:
Does this plan contain genuine interview preparation relevant
to the {role} (e.g., DSA, system design, SQL, case studies,
ML design, security scenarios, etc.)?

1c. portfolio (0-9)
QUESTION:
Will this user have a strong, role-relevant portfolio that demonstrates
real capability to employers?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

D2: TCF — Time-Constrained Feasibility (Max 15)

2a. feasibility (0-5)
QUESTION:
Is the scope achievable within the available time?

2b. cognitive_load (0-5)
QUESTION:
Is the progression manageable and not overwhelming?

2c. appropriateness (0-5)
QUESTION:
Are topics appropriate for the user's level and timeline?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

D3: PPA — Personalization & Preference Alignment (Max 15)

3a. experience_adaptation (0-5)
QUESTION:
Does this plan reflect the user's actual background?

3b. preference_integration (0-5)
QUESTION:
Does the plan reflect the user's stated preferences and constraints?

3c. stack_relevance (0-5)
QUESTION:
Are the chosen technologies appropriate for the {role}
and the user's background?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

D4: MA — Market Alignment (Max 10)

4a. skill_demand (0-5)
QUESTION:
Do the skills match current job market demand for the {role}?

4b. global_alignment (0-5)
QUESTION:
Will this plan make the user competitive in the global job market?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

D5: SPQ — Strategic Prioritization Quality (Max 10)

5a. high_roi (0-5)
QUESTION:
Does the plan focus on high-impact skills for getting hired
in the {role}?

5b. progression (0-5)
QUESTION:
Is there a logical progression from basics → applied → job-ready?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

D6: CSDC — Curriculum Structural Depth & Clarity (Max 15)

(Same logic as original — unchanged)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

D7: CER — Career Execution Readiness (Max 10)

(Same logic as original — unchanged)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — SCORING PROCESS (Follow Exactly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(Same as original — unchanged)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 7 — REQUIRED JSON OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY the JSON below. No text before or after it.

{{
"penalties_applied": [],
"HRO": {{"score": 0, "breakdown": {{"core_technical": 0, "interview_prep": 0, "portfolio": 0}}, "comment": ""}},
"TCF": {{"score": 0, "breakdown": {{"feasibility": 0, "cognitive_load": 0, "appropriateness": 0}}, "comment": ""}},
"PPA": {{"score": 0, "breakdown": {{"experience_adaptation": 0, "preference_integration": 0, "stack_relevance": 0}}, "comment": ""},
"MA": {{"score": 0, "breakdown": {{"skill_demand": 0, "global_alignment": 0}}, "comment": ""}},
"SPQ": {{"score": 0, "breakdown": {{"high_roi": 0, "progression": 0}}, "comment": ""}},
"CSDC": {{"score": 0, "breakdown": {{"knowledge_progression": 0, "content_specificity": 0, "actionability": 0}}, "comment": ""}},
"CER": {{"score": 0, "breakdown": {{"resume": 0, "mock_interviews": 0, "application_strategy": 0}}, "comment": ""}},
"Total_Score": 0,
"score_band": "Exceptional | Good | Average | Weak | Poor",
"overall_summary": ""
}}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 8 — LEARNING PLAN TO EVALUATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{plan}
"""

# ============================================================
# SCORE VALIDATION
# ============================================================

def validate_scores(result, plan_label):
    """
    Validates that all scores are within stated maximums
    and that breakdown sums match dimension totals.
    Returns a list of error strings. Empty list = valid.
    """
    errors = []
    total_check = 0

    for dim, limits in DIMENSION_MAXES.items():
        if dim not in result:
            errors.append(f"{plan_label} — Missing dimension: {dim}")
            continue

        score = result[dim].get("score", -1)

        # Dimension max check
        if score > limits["max"]:
            errors.append(
                f"{plan_label} {dim}: score {score} exceeds max {limits['max']}"
            )

        # Subcriterion checks
        breakdown = result[dim].get("breakdown", {})
        breakdown_sum = 0

        for sub, sub_max in limits["breakdown"].items():
            sub_score = breakdown.get(sub, -1)

            if sub_score < 0:
                errors.append(
                    f"{plan_label} {dim}.{sub}: missing from breakdown"
                )
                continue

            if sub_score > sub_max:
                errors.append(
                    f"{plan_label} {dim}.{sub}: {sub_score} exceeds max {sub_max}"
                )

            breakdown_sum += sub_score

        # Breakdown sum vs dimension score
        if breakdown_sum != score:
            errors.append(
                f"{plan_label} {dim}: breakdown sum {breakdown_sum} "
                f"does not match score {score}"
            )

        total_check += score

    # Total score check
    reported_total = result.get("Total_Score", -1)
    if reported_total != total_check:
        errors.append(
            f"{plan_label} Total_Score: reported {reported_total} "
            f"but dimension sum is {total_check}"
        )

    return errors


# ============================================================
# SINGLE PLAN EVALUATOR
# ============================================================

def evaluate_single_plan(plan, plan_label, user_prefs, max_retries=3):
    """
    Evaluates one plan independently against the HROP rubric.
    Returns (result_dict, response_object) or (None, None) on failure.
    """
    prompt = EVALUATION_PROMPT.format(
        user_preferences=json.dumps(user_prefs, indent=2),
        plan=json.dumps(plan, indent=2),
        role=user_prefs["role"]
    )

    for attempt in range(max_retries):
        try:
            print(f"  [{plan_label}] API call — attempt {attempt + 1} of {max_retries}...")

            response = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_MESSAGE
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            raw_text = response.choices[0].message.content
            result = json.loads(raw_text)

            # Validate scores
            errors = validate_scores(result, plan_label)

            if errors:
                print(f"  [{plan_label}] Validation errors on attempt {attempt + 1}:")
                for e in errors:
                    print(f"    - {e}")

                if attempt < max_retries - 1:
                    print(f"  Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                else:
                    print(
                        f"  WARNING: [{plan_label}] has unresolved validation "
                        f"errors after {max_retries} attempts. Saving with errors."
                    )

            return result, response

        except json.JSONDecodeError as e:
            print(f"  [{plan_label}] JSON parse error on attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)

        except Exception as e:
            print(f"  [{plan_label}] API error on attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)

    print(f"  [{plan_label}] All {max_retries} attempts failed.")
    return None, None


# ============================================================
# DIMENSION SUMMARY PRINTER
# ============================================================

def print_dimension_summary(result_1, result_2):
    """Prints a clean side-by-side dimension comparison to console."""
    print("\n" + "=" * 55)
    print("DIMENSION BREAKDOWN")
    print("=" * 55)
    print(f"{'Dimension':<8} {'Plan1 (System)':>14} {'Plan2 (Baseline)':>16} {'Max':>5}")
    print("-" * 55)

    for dim, limits in DIMENSION_MAXES.items():
        s1 = result_1[dim]["score"] if result_1 else "ERR"
        s2 = result_2[dim]["score"] if result_2 else "ERR"
        mx = limits["max"]
        print(f"{dim:<8} {str(s1):>14} {str(s2):>16} {mx:>5}")

    print("-" * 55)
    t1 = result_1.get("Total_Score", "ERR") if result_1 else "ERR"
    t2 = result_2.get("Total_Score", "ERR") if result_2 else "ERR"
    print(f"{'TOTAL':<8} {str(t1):>14} {str(t2):>16} {'100':>5}")
    print("=" * 55)


# ============================================================
# MAIN
# ============================================================

def main():

    # --- Load plans ---
    try:
        with open("plan_1.json", "r", encoding="utf-8") as f:
            plan_1 = json.load(f)
        with open("plan_2.json", "r", encoding="utf-8") as f:
            plan_2 = json.load(f)
    except FileNotFoundError as e:
        print(f"\nERROR: Could not load plan file — {e}")
        print("Make sure plan_1.json and plan_2.json exist in the same directory.")
        return

    print("\n" + "=" * 55)
    print("HROP AI EVALUATION — GPT Independent Scoring")
    print(f"Model          : {MODEL}")
    print(f"Temperature    : {TEMPERATURE}")
    print(f"Prompt Version : {PROMPT_VERSION}")
    print(f"Evaluation Type: Independent per plan (unbiased)")
    print("=" * 55 + "\n")

    # --- Evaluate Plan 1 (System Output) ---
    print("Evaluating Plan 1 (System Output)...")
    result_1, response_1 = evaluate_single_plan(
        plan_1, "Plan_1_System", user_preferences
    )

    # --- Evaluate Plan 2 (Baseline Output) ---
    print("\nEvaluating Plan 2 (Baseline Output)...")
    result_2, response_2 = evaluate_single_plan(
        plan_2, "Plan_2_Baseline", user_preferences
    )

    if result_1 is None or result_2 is None:
        print("\nEvaluation failed for one or both plans. Review errors above.")
        return

    # --- Determine better plan ---
    score_1 = result_1.get("Total_Score", 0)
    score_2 = result_2.get("Total_Score", 0)
    gap     = abs(score_1 - score_2)

    if score_1 > score_2:
        better_plan    = "Plan_1_System"
        worse_plan     = "Plan_2_Baseline"
    elif score_2 > score_1:
        better_plan    = "Plan_2_Baseline"
        worse_plan     = "Plan_1_System"
    else:
        better_plan    = "Tie"
        worse_plan     = "Tie"

    gap_assessment = (
        "Strong discrimination (gap >= 15)"   if gap >= 15 else
        "Moderate discrimination (gap 8-14)"  if gap >= 8  else
        "Weak discrimination (gap < 8) — consider reviewing calibration"
    )

    # --- Build final output ---
    final_output = {
        "evaluation_metadata": {
            "model_used":        response_1.model,
            "prompt_version":    PROMPT_VERSION,
            "temperature":       TEMPERATURE,
            "evaluation_type":   "independent_per_plan_unbiased",
            "bias_mitigation":   "outcome_focused_rubric_v3",
            "timestamp":         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "candidate_role":    user_preferences["role"],
            "prep_months":       user_preferences["preparation_time_months"],
            "study_hrs_per_day": user_preferences["study_hours_per_day"],
            "tokens": {
                "plan1_prompt_tokens":     response_1.usage.prompt_tokens,
                "plan1_completion_tokens": response_1.usage.completion_tokens,
                "plan2_prompt_tokens":     response_2.usage.prompt_tokens,
                "plan2_completion_tokens": response_2.usage.completion_tokens,
            }
        },
        "Plan_1_System":   result_1,
        "Plan_2_Baseline": result_2,
        "comparison": {
            "better_plan":      better_plan,
            "Plan_1_Total":     score_1,
            "Plan_2_Total":     score_2,
            "score_gap":        gap,
            "gap_assessment":   gap_assessment,
            "score_band_plan1": result_1.get("score_band", "N/A"),
            "score_band_plan2": result_2.get("score_band", "N/A"),
            "penalties_plan1":  result_1.get("penalties_applied", []),
            "penalties_plan2":  result_2.get("penalties_applied", []),
        }
    }

    # --- Save output ---
    output_file = "evaluation_result_gpt_v3.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    # --- Console summary ---
    print_dimension_summary(result_1, result_2)

    print(f"\nRESULTS SUMMARY")
    print(f"Plan 1 (System)   : {score_1}/100  [{result_1.get('score_band', 'N/A')}]")
    print(f"Plan 2 (Baseline) : {score_2}/100  [{result_2.get('score_band', 'N/A')}]")
    print(f"Score Gap         : {gap} points")
    print(f"Better Plan       : {better_plan}")
    print(f"Gap Assessment    : {gap_assessment}")
    print(f"\nPenalties on Plan 1 : {result_1.get('penalties_applied', [])}")
    print(f"Penalties on Plan 2 : {result_2.get('penalties_applied', [])}")
    print(f"\nSaved to {output_file}")
    print("\nSummaries:")
    print(f"Plan 1: {result_1.get('overall_summary', '')}")
    print(f"Plan 2: {result_2.get('overall_summary', '')}")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()