import json
import os
from datetime import datetime
import anthropic

# =====================================
# CONFIGURATION
# =====================================

# Set your Anthropic API key as an environment variable:
# export ANTHROPIC_API_KEY="your-key-here"
client = anthropic.Anthropic(api_key=("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"))

MODEL = "claude-sonnet-4-6"
TEMPERATURE = 0.0
PROMPT_VERSION = "v1.0-comparative-dimension-first"

PLAN_1_FILE = "plan_1.json"
PLAN_2_FILE = "plan_2.json"
OUTPUT_FILE = "evaluation_result_Claude.json"

# =====================================
# USER PROFILE
# =====================================

USER_PROFILE = {
    "role": "Computer Vision Engineer",
    "experience": "University Recent CSE Graduate",
    "preparation_time_months": 5,
    "study_hours_per_day": 1,
    "Market_Focus": "Global",
    "other_preferences": "Intermediate (Built small projects) coding experience, familiar with python, java, C, C++ Language and familiar with Tensorflow,Pytorch Framework. build some academic projects. passionate in harware software integration work"
}

# =====================================
# SCORING WEIGHTS
# =====================================

WEIGHTS = {
    "D1_HRO": 25,
    "D2_TCF": 15,
    "D3_PPA": 15,
    "D4_MA":  10,
    "D5_SPQ": 10,
    "D6_CSDC": 15,
    "D7_CER": 10
}

# =====================================
# SYSTEM PROMPT
# =====================================

SYSTEM_PROMPT = """You are a strict expert evaluator of AI-generated learning plans for tech career preparation.
Your job is to compare two plans HEAD-TO-HEAD on each evaluation dimension.

For every dimension you must:
  1. Analyze both plans together on that dimension
  2. Identify which performs better and clearly explain why
  3. Assign scores that are CONSISTENT with your comparative analysis

Score consistency rule: if Plan 1/Plan 2 is clearly stronger on a dimension, its score
must be meaningfully higher. The score gap must match
the strength of your written analysis.

Be realistic with penalties. The main goal is making the user job-ready within
the given constraints. Do not penalize harshly for minor omissions. Penalize
significantly only when a gap materially reduces hiring readiness or feasibility.

Your evaluation criteria must be interpreted relative to the user's target role — what counts as interview-ready, portfolio-complete, or market-aligned differs meaningfully between Software Engineering, Data Analytics, and AI Engineering roles.

Output strict JSON only. No markdown. No commentary outside the JSON structure."""

# =====================================
# EVALUATION PROMPT
# =====================================

EVALUATION_PROMPT = """You will evaluate TWO AI-generated learning plans by comparing them head-to-head on each dimension.

========================
USER PROFILE
========================
{user_profile}

========================
PLAN 1
========================
{plan1}

========================
PLAN 2
========================
{plan2}

========================
EVALUATION METHODOLOGY
========================
For each of the 7 dimensions below:
  - comparative_analysis: explain how both plans differ on this dimension (3–5 sentences)
  - dimension_winner: "Plan_1" or "Plan_2" or "Tie"
  - winner_reason: one sentence stating the decisive factor
  - Then assign subcriteria scores for each plan that match your analysis

========================
SCORING RUBRIC
========================

D1 — Hiring Readiness Optimization (weight 25%, max raw 25):
  Subcriteria:
  - core_technical_readiness (0-8): Covers required stack? Depth appropriate for graduate level?
  - interview_prep_readiness (0-8): Role-relevant interview preparation scheduled early and consistently? For SWE: DSA, system design, behavioral. For DA/Analytics: SQL challenges, case study walkthroughs, business problem framing, behavioral. For AI Engineering: ML system design, coding, behavioral.
  - portfolio_project_strength (0-9): Progressive capstone present? Final project employer-worthy for the target role? Deployment expected for SWE; published notebook, dashboard, or model card acceptable for DA/Analytics and AI Engineering roles.

D2 — Time-Constrained Feasibility (weight 15%, max raw 15):
  Subcriteria:
  - hour_compliance (0–5): Total planned hours fit within available hours? Buffer present?
  - cognitive_load_realism (0–5): Each week achievable in allotted hours? No skill-stacking?
  - overengineering_avoidance (0–5): No advanced topics that don't fit the timeline or role level?

D3 — Personalization & Preference Alignment (weight 15%, max raw 15):
  Subcriteria:
  - experience_adaptation (0–5): Skips beginner content? Matches user's actual experience level?
  - preference_integration (0–5): Uses user's stated stack, role focus, and market target?
  - stack_justification_quality (0–5): Technology choices explained and tied to user's goal?

D4 — Market Alignment (weight 10%, max raw 10):
  Subcriteria:
  - skill_demand_relevance (0-5): Skills taught actually in demand for this role globally? Award extra credit toward the upper end (4–5) if the plan incorporates emerging or advanced tools (e.g. LLM tooling, dbt, cloud-native) where the timeline realistically permits — not as a requirement, but as a differentiator.
  - regional_global_alignment (0-5): Reflects what global employers hire for at graduate level for the target role — e.g. SQL + BI tools for DA/Analytics, cloud + system design for SWE, MLOps + Python for AI Engineering?

D5 — Strategic Prioritization Quality (weight 10%, max raw 10):
  Subcriteria:
  - high_roi_topics_prioritized (0-5): Highest-impact skills taught first, not last?
  - logical_phasing (0-5): Follows a coherent role-appropriate phasing arc? E.g. Foundation → Applied → Interview for SWE; SQL/Stats Foundation → BI Tool + EDA → Business Problem + Presentation for DA/Analytics; ML Theory → Experimentation → Production for AI Engineering. Penalize only when phases are genuinely illogical, not merely different from the SWE arc.

D6 — Curriculum Structural Depth & Clarity (weight 15%, max raw 15):
  Subcriteria:
  - logical_module_ordering (0–5): Modules build on each other correctly?
  - meaningful_subtopic_detail (0–5): Subtopics specific and actionable, not vague lists?
  - clear_learning_outcomes (0–5): Each week/module has a measurable deliverable or outcome?

D7 — Career Execution Readiness (weight 10%, max raw 10):
  Subcriteria:
  - resume_linkedin_preparation (0–4): Resume/LinkedIn work scheduled explicitly, not as afterthought?
  - mock_interviews_included (0–3): Role-relevant mock interviews explicitly planned? For SWE: coding + system design + behavioral. For DA/Analytics: SQL challenge + case study walkthrough + behavioral. For AI Engineering: ML system design + coding + behavioral.
  - application_strategy (0–3): Job application plan: platforms, timing, volume, networking?

========================
WEIGHTED SCORE FORMULA
========================
For each dimension:
  weighted_contribution = (raw_score / max_raw) * weight * 100

total_weighted_score = sum of all 7 weighted_contributions  (out of 100)

========================
OUTPUT FORMAT (strict JSON, no markdown)
========================
{{
  "evaluation_methodology": "comparative — both plans analyzed together per dimension before scoring",
  "user_profile_summary": "",
  "dimensions": {{
    "D1": {{
      "name": "Hiring Readiness Optimization",
      "weight": 0.25,
      "comparative_analysis": "",
      "dimension_winner": "",
      "winner_reason": "",
      "Plan_1": {{
        "subcriteria": {{
          "core_technical_readiness": {{"score": 0, "max": 8, "justification": ""}},
          "interview_prep_readiness": {{"score": 0, "max": 8, "justification": ""}},
          "portfolio_project_strength": {{"score": 0, "max": 9, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 25,
        "weighted_contribution": 0.0
      }},
      "Plan_2": {{
        "subcriteria": {{
          "core_technical_readiness": {{"score": 0, "max": 8, "justification": ""}},
          "interview_prep_readiness": {{"score": 0, "max": 8, "justification": ""}},
          "portfolio_project_strength": {{"score": 0, "max": 9, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 25,
        "weighted_contribution": 0.0
      }}
    }},
    "D2": {{
      "name": "Time-Constrained Feasibility",
      "weight": 0.15,
      "comparative_analysis": "",
      "dimension_winner": "",
      "winner_reason": "",
      "Plan_1": {{
        "subcriteria": {{
          "hour_compliance": {{"score": 0, "max": 5, "justification": ""}},
          "cognitive_load_realism": {{"score": 0, "max": 5, "justification": ""}},
          "overengineering_avoidance": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 15,
        "weighted_contribution": 0.0
      }},
      "Plan_2": {{
        "subcriteria": {{
          "hour_compliance": {{"score": 0, "max": 5, "justification": ""}},
          "cognitive_load_realism": {{"score": 0, "max": 5, "justification": ""}},
          "overengineering_avoidance": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 15,
        "weighted_contribution": 0.0
      }}
    }},
    "D3": {{
      "name": "Personalization & Preference Alignment",
      "weight": 0.15,
      "comparative_analysis": "",
      "dimension_winner": "",
      "winner_reason": "",
      "Plan_1": {{
        "subcriteria": {{
          "experience_adaptation": {{"score": 0, "max": 5, "justification": ""}},
          "preference_integration": {{"score": 0, "max": 5, "justification": ""}},
          "stack_justification_quality": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 15,
        "weighted_contribution": 0.0
      }},
      "Plan_2": {{
        "subcriteria": {{
          "experience_adaptation": {{"score": 0, "max": 5, "justification": ""}},
          "preference_integration": {{"score": 0, "max": 5, "justification": ""}},
          "stack_justification_quality": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 15,
        "weighted_contribution": 0.0
      }}
    }},
    "D4": {{
      "name": "Market Alignment",
      "weight": 0.10,
      "comparative_analysis": "",
      "dimension_winner": "",
      "winner_reason": "",
      "Plan_1": {{
        "subcriteria": {{
          "skill_demand_relevance": {{"score": 0, "max": 5, "justification": ""}},
          "regional_global_alignment": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 10,
        "weighted_contribution": 0.0
      }},
      "Plan_2": {{
        "subcriteria": {{
          "skill_demand_relevance": {{"score": 0, "max": 5, "justification": ""}},
          "regional_global_alignment": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 10,
        "weighted_contribution": 0.0
      }}
    }},
    "D5": {{
      "name": "Strategic Prioritization Quality",
      "weight": 0.10,
      "comparative_analysis": "",
      "dimension_winner": "",
      "winner_reason": "",
      "Plan_1": {{
        "subcriteria": {{
          "high_roi_topics_prioritized": {{"score": 0, "max": 5, "justification": ""}},
          "logical_phasing": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 10,
        "weighted_contribution": 0.0
      }},
      "Plan_2": {{
        "subcriteria": {{
          "high_roi_topics_prioritized": {{"score": 0, "max": 5, "justification": ""}},
          "logical_phasing": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 10,
        "weighted_contribution": 0.0
      }}
    }},
    "D6": {{
      "name": "Curriculum Structural Depth & Clarity",
      "weight": 0.15,
      "comparative_analysis": "",
      "dimension_winner": "",
      "winner_reason": "",
      "Plan_1": {{
        "subcriteria": {{
          "logical_module_ordering": {{"score": 0, "max": 5, "justification": ""}},
          "meaningful_subtopic_detail": {{"score": 0, "max": 5, "justification": ""}},
          "clear_learning_outcomes": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 15,
        "weighted_contribution": 0.0
      }},
      "Plan_2": {{
        "subcriteria": {{
          "logical_module_ordering": {{"score": 0, "max": 5, "justification": ""}},
          "meaningful_subtopic_detail": {{"score": 0, "max": 5, "justification": ""}},
          "clear_learning_outcomes": {{"score": 0, "max": 5, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 15,
        "weighted_contribution": 0.0
      }}
    }},
    "D7": {{
      "name": "Career Execution Readiness",
      "weight": 0.10,
      "comparative_analysis": "",
      "dimension_winner": "",
      "winner_reason": "",
      "Plan_1": {{
        "subcriteria": {{
          "resume_linkedin_preparation": {{"score": 0, "max": 4, "justification": ""}},
          "mock_interviews_included": {{"score": 0, "max": 3, "justification": ""}},
          "application_strategy": {{"score": 0, "max": 3, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 10,
        "weighted_contribution": 0.0
      }},
      "Plan_2": {{
        "subcriteria": {{
          "resume_linkedin_preparation": {{"score": 0, "max": 4, "justification": ""}},
          "mock_interviews_included": {{"score": 0, "max": 3, "justification": ""}},
          "application_strategy": {{"score": 0, "max": 3, "justification": ""}}
        }},
        "raw_score": 0,
        "max_raw": 10,
        "weighted_contribution": 0.0
      }}
    }}
  }},
  "final_scores": {{
    "Plan_1": {{
      "total_weighted_score": 0.0,
      "dimension_wins": [],
      "strengths": [],
      "critical_gaps": []
    }},
    "Plan_2": {{
      "total_weighted_score": 0.0,
      "dimension_wins": [],
      "strengths": [],
      "critical_gaps": []
    }}
  }},
  "verdict": {{
    "winner": "Plan_1 or Plan_2",
    "score_gap": 0.0,
    "margin_interpretation": "narrow / moderate / decisive",
    "winner_key_advantages": [],
    "loser_salvageable_strengths": [],
    "shared_gaps_in_both_plans": [],
    "final_recommendation": ""
  }}
}}"""

# =====================================
# WEIGHTED SCORE CALCULATOR
# =====================================

def calculate_weighted_scores(result: dict) -> dict:
    """
    Recalculates weighted_contribution and total_weighted_score
    from raw subcriteria scores, as a verification layer on top
    of what the model returns.
    """
    dimension_config = {
        "D1": {"weight": 0.25, "max_raw": 25},
        "D2": {"weight": 0.15, "max_raw": 15},
        "D3": {"weight": 0.15, "max_raw": 15},
        "D4": {"weight": 0.10, "max_raw": 10},
        "D5": {"weight": 0.10, "max_raw": 10},
        "D6": {"weight": 0.15, "max_raw": 15},
        "D7": {"weight": 0.10, "max_raw": 10},
    }

    dims = result.get("dimensions", {})
    totals = {"Plan_1": 0.0, "Plan_2": 0.0}

    for dim_key, cfg in dimension_config.items():
        if dim_key not in dims:
            continue
        for plan_key in ["Plan_1", "Plan_2"]:
            plan_dim = dims[dim_key].get(plan_key, {})
            subcriteria = plan_dim.get("subcriteria", {})
            raw = sum(v.get("score", 0) for v in subcriteria.values())
            contribution = round((raw / cfg["max_raw"]) * cfg["weight"] * 100, 2)
            plan_dim["raw_score"] = raw
            plan_dim["weighted_contribution"] = contribution
            totals[plan_key] += contribution

    for plan_key in ["Plan_1", "Plan_2"]:
        result.setdefault("final_scores", {}).setdefault(plan_key, {})
        result["final_scores"][plan_key]["total_weighted_score"] = round(totals[plan_key], 2)

    # Recalculate score gap in verdict
    gap = round(abs(totals["Plan_1"] - totals["Plan_2"]), 2)
    result.setdefault("verdict", {})["score_gap"] = gap

    winner = "Plan_1" if totals["Plan_1"] >= totals["Plan_2"] else "Plan_2"
    result["verdict"]["winner"] = winner

    if gap <= 5:
        result["verdict"]["margin_interpretation"] = "narrow"
    elif gap <= 15:
        result["verdict"]["margin_interpretation"] = "moderate"
    else:
        result["verdict"]["margin_interpretation"] = "decisive"

    return result

# =====================================
# EVALUATION FUNCTION
# =====================================

def evaluate_pairwise(plan1: dict, plan2: dict) -> dict:
    prompt = EVALUATION_PROMPT.format(
        user_profile=json.dumps(USER_PROFILE, indent=2),
        plan1=json.dumps(plan1, indent=2),
        plan2=json.dumps(plan2, indent=2)
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw_text = response.content[0].text.strip()

    # Strip accidental markdown fences if model adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    result = json.loads(raw_text)

    # Verify and recalculate scores as a safety layer
    result = calculate_weighted_scores(result)

    return result

# =====================================
# PRETTY PRINT SUMMARY
# =====================================

def print_summary(result: dict) -> None:
    verdict = result.get("verdict", {})
    final = result.get("final_scores", {})
    dims = result.get("dimensions", {})

    print("\n" + "="*50)
    print("EVALUATION COMPLETE")
    print("="*50)
    print(f"Plan 1 Score : {final.get('Plan_1', {}).get('total_weighted_score', 'N/A')} / 100")
    print(f"Plan 2 Score : {final.get('Plan_2', {}).get('total_weighted_score', 'N/A')} / 100")
    print(f"Winner       : {verdict.get('winner', 'N/A')}")
    print(f"Score Gap    : {verdict.get('score_gap', 'N/A')} points ({verdict.get('margin_interpretation', '')})")

    print("\nDimension Breakdown:")
    print(f"  {'Dimension':<35} {'Plan 1':>8} {'Plan 2':>8} {'Winner'}")
    print(f"  {'-'*35} {'-'*8} {'-'*8} {'-'*10}")
    for key, dim in dims.items():
        p1 = dim.get("Plan_1", {}).get("weighted_contribution", 0)
        p2 = dim.get("Plan_2", {}).get("weighted_contribution", 0)
        w = dim.get("dimension_winner", "")
        name = dim.get("name", key)
        print(f"  {name:<35} {p1:>8.2f} {p2:>8.2f} {w}")

    print(f"\nFinal Recommendation:")
    print(f"  {verdict.get('final_recommendation', '')}")
    print("="*50)

# =====================================
# MAIN
# =====================================

def main():
    try:
        with open(PLAN_1_FILE, "r", encoding="utf-8") as f:
            plan1 = json.load(f)
        with open(PLAN_2_FILE, "r", encoding="utf-8") as f:
            plan2 = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure plan_1.json and plan_2.json exist in the working directory.")
        return
    except json.JSONDecodeError as e:
        print(f"JSON parse error in plan files: {e}")
        return

    print("Running comparative pairwise evaluation...")
    print(f"Model    : {MODEL}")
    print(f"Version  : {PROMPT_VERSION}")

    result = evaluate_pairwise(plan1, plan2)

    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "model": MODEL,
        "temperature": TEMPERATURE,
        "prompt_version": PROMPT_VERSION,
        "user_profile": USER_PROFILE,
        "result": result,
        "winner": result.get("verdict", {}).get("winner", "Unknown"),
        "plan_1_score": result.get("final_scores", {}).get("Plan_1", {}).get("total_weighted_score", 0),
        "plan_2_score": result.get("final_scores", {}).get("Plan_2", {}).get("total_weighted_score", 0),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print_summary(result)
    print(f"\nFull output saved to: {OUTPUT_FILE}")

# =====================================

if __name__ == "__main__":
    main()