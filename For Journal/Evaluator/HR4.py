import json
import os
import time
from datetime import datetime
import anthropic

# Initialize Anthropic client (Replace with your actual Anthropic API key)
client         = anthropic.Anthropic(api_key="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")
MODEL          = "claude-sonnet-4-6" # Update to the exact model string once available
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
- Uses structured formatting, headers, or JSON-like presentation
- Explicitly states numbers such as hours or weeks
- Uses professional terminology or labels
- Is longer or more verbose than another plan

DO reward a plan because it:
- Genuinely prepares the user for the target role
- Is realistically achievable given the user's constraints
- Reflects the user's actual background and preferences
- Contains actionable, specific guidance
- Aligns with real job market demands

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — FUNDAMENTAL SCORING RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. BOTTOM-UP SCORING (mandatory):
   Step 1 → Score each subcriterion individually first.
   Step 2 → Sum subcriteria to get the dimension total.
   Step 3 → Sum all dimensions to get Total_Score.
   Never decide the total first and reverse-engineer breakdowns.

2. Score the SUBSTANCE of guidance, not its presentation style.
   If a plan achieves an outcome implicitly rather than explicitly,
   award partial credit proportional to how well it is achieved.

3. Apply penalty deductions ONLY when a component is ENTIRELY
   ABSENT from the plan. Partial presence = partial credit, NOT a penalty.

4. Breakdown scores MUST sum exactly to the dimension score.
   No subcriterion may exceed its stated maximum.

5. Do NOT inflate scores. If uncertain, score lower.

6. Return ONLY valid JSON. No text or explanation outside the JSON.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2 — USER PROFILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{user_preferences}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — CALIBRATION ANCHORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Read these carefully before scoring. They define what each score
band looks like in terms of OUTCOMES, not formatting.

88-100 (Exceptional):
A plan at this level would make a hiring manager genuinely confident
the candidate followed it. It covers the right technical skills at
the right depth for an AI Engineer. It includes meaningful, specific
projects relevant to the role. It prepares the user for actual
interviews with concrete practice mechanisms. It gives the user a
real job search strategy. The scope is achievable in 6 months for
a 3rd year CSE student with basic coding experience.

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
    (no mention of timeline, pacing, phases, or study allocation)
    → Deduct 4 from TCF: feasibility capped at 1

P2: No interview preparation content of any kind
    (no DSA, system design, behavioral prep, or mock interview mention)
    → Deduct 5 from HRO: interview_prep capped at 3

P3: No project or applied work of any kind
    (no mention of building, implementing, or hands-on practice)
    → Deduct 5 from HRO: portfolio capped at 4

P4: No connection to the user's specific background
    (plan is identical to what you would give any random beginner)
    → Deduct 4 from PPA: experience_adaptation capped at 1

P5: No career execution content of any kind
    (no mention of resume, job applications, or job search strategy)
    → Deduct 5 from CER: all subcriteria capped at 1 each

P6: Scope is clearly impossible for the stated timeline
    (6 months, 3 hrs/day; content volume would realistically take 2+ years)
    → Deduct 4 from TCF: cognitive_load capped at 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — SCORING MATRIX (OUTCOME-FOCUSED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each subcriterion, a guiding QUESTION is provided.
Answer the question honestly, then assign the score.
Evaluate SUBSTANCE, not structure or formatting.

──────────────────────────────────────────
D1: HRO — Hiring Readiness Optimization (Max 25)
──────────────────────────────────────────

1a. core_technical (0-8)
QUESTION: If this user follows this plan completely, will they
have the technical skills to pass a technical interview for an
AI Engineer role in the global market?

8   → Yes, confidently. Full AI Engineer stack covered at production
      depth: ML frameworks (PyTorch or TensorFlow), model deployment,
      APIs, cloud basics, MLOps fundamentals. All critical areas present.
6-7 → Yes, with minor gaps. Most critical skills present but 1-2
      important areas are shallow or missing.
4-5 → Partially. Core ML skills present but deployment, cloud, or
      MLOps missing entirely.
2-3 → Unlikely. Only foundational or theoretical skills covered.
0-1 → No. Plan does not prepare for a technical AI Engineer interview.

1b. interview_prep (0-8)
QUESTION: Does this plan contain genuine interview preparation
content that will help the user pass real interviews?
Evaluate the substance of preparation, not how it is scheduled.

8   → Covers DSA problem patterns (not just "learn DSA"), ML system
      design questions, AND behavioral preparation (STAR method or
      similar). Practice mechanisms are specified. Preparation begins
      early and is not limited to the final weeks.
6-7 → Strong coverage of 2 out of 3 interview types. Minor gaps in
      one area or timing is slightly late.
4-5 → One interview type well covered. Others mentioned only vaguely
      or in passing.
2-3 → Interview prep mentioned but no actionable guidance given.
      Student would not know what to actually practice.
0-1 → Entirely absent or only a single passing mention.

1c. portfolio (0-9)
QUESTION: Will this user have a genuinely impressive portfolio
project that demonstrates real AI Engineering capability to a recruiter?
Evaluate project quality and relevance, not formatting.

9   → Specific, impressive project clearly defined. Directly relevant
      to AI Engineer role. Built progressively over time. Involves real
      data, model training, deployment, API integration, or a combination.
      A recruiter seeing this would be impressed.
7-8 → Good project with clear scope. Minor gap such as deployment not
      mentioned but the rest of the project is strong and specific.
5-6 → Project present but vaguely defined OR scope is too small to
      impress a hiring manager. Student knows roughly what to build
      but lacks critical details.
3-4 → "Build a project" or similar mentioned without any specification
      of what to build, what data to use, or what it should demonstrate.
0-2 → No project component at all.

──────────────────────────────────────────
D2: TCF — Time-Constrained Feasibility (Max 15)
──────────────────────────────────────────
Context: User has 6 months at ~3 hrs/day ≈ 430 total hours available.

2a. feasibility (0-5)
QUESTION: Is the scope of this plan genuinely achievable in the
available time, regardless of how time is expressed in the plan?

5   → Scope is clearly achievable. Content volume matches what a
      focused 3rd year CSE student can realistically learn in 430 hours.
      The plan does not try to teach everything. Selective and strategic.
4   → Mostly achievable. Slightly ambitious but realistic for a
      motivated and disciplined student.
3   → Somewhat achievable with significant prioritization cuts by the
      student. Borderline between realistic and overloaded.
1-2 → Scope is too large. Realistically would take 12 or more months.
0   → Entirely unrealistic. Years worth of content compressed into 6 months.

2b. cognitive_load (0-5)
QUESTION: Is the learning progression gradual enough to avoid
overwhelming a 3rd year CSE student who has basic coding experience?

5   → Topics introduced at a pace appropriate for the experience level.
      Builds from familiar territory to unfamiliar. No abrupt complexity
      jumps. Student can follow the sequence without feeling lost.
4   → Mostly well-paced. One or two abrupt transitions but overall
      progression is manageable.
3   → Uneven pacing. Some sections rush through complex topics without
      adequate preparation.
1-2 → Significant pacing problems throughout. Repeatedly jumps from
      basic to advanced without scaffolding.
0   → No consideration of learning pace or cognitive load whatsoever.

2c. appropriateness (0-5)
QUESTION: Are all topics in this plan appropriate for a 3rd year CSE
student targeting an AI Engineer role within a 6-month timeline?

5   → All topics are well-matched to the experience level and timeline.
      No research-level, premature advanced, or unnecessary topics.
      Every topic serves a clear purpose for the goal.
4   → Mostly appropriate. One or two borderline advanced topics that
      could be justified for this role.
3   → Several topics are premature for this profile or timeline.
      Some padding or irrelevant advanced content.
1-2 → Plan is significantly overengineered for this user's level and time.
0   → Completely inappropriate difficulty level for a beginner-intermediate
      student in a 6-month window.

──────────────────────────────────────────
D3: PPA — Personalization & Preference Alignment (Max 15)
──────────────────────────────────────────

3a. experience_adaptation (0-5)
QUESTION: Does this plan genuinely reflect that the user is a
3rd year CSE student with basic coding experience who wants a
part-time job? Or is it generic enough to give to any beginner?

5   → Plan clearly adapted to this specific profile. Skips basic CS
      concepts the user already knows. Acknowledges part-time job goal
      and plans realistically around it. Appropriate depth throughout
      for someone at the beginner-intermediate level.
4   → Well adapted with minor generic sections that could apply broadly.
3   → Partially adapted. Several sections feel generic and not specific
      to this user's situation.
1-2 → Minimal adaptation. Mostly generic beginner-level content that
      does not reflect this user's actual starting point.
0   → No evidence of adaptation. Generic plan that could apply to anyone.

3b. preference_integration (0-5)
QUESTION: Does the plan genuinely reflect the user's stated preferences?
(Python as primary language, Node.js and React familiarity,
AI Engineer focus, global market, part-time job goal)

5   → Python used throughout as the primary language. Prior Node.js and
      React knowledge is leveraged meaningfully, for example for API or
      frontend integration of ML models. AI Engineer role is the clear
      and consistent focus throughout. Part-time goal is acknowledged.
4   → Most preferences reflected in the content. Minor gaps in one area.
3   → Python used but other stated preferences largely ignored throughout.
1-2 → Preferences acknowledged in an introduction or overview but not
      actually reflected in the plan content or technology choices.
0   → No reflection of any stated user preferences.

3c. stack_relevance (0-5)
QUESTION: Are the technology choices genuinely right for this user's
background and goal? Does the plan make sensible choices even if it
does not provide written explanations for them?

5   → Every technology choice is the right tool for this specific user's
      situation. Stack is coherent, Python-first, and appropriate for
      AI Engineering in the global market. Choices make sense given
      what the user already knows.
4   → Mostly good choices. One or two questionable technology selections
      that could have been better matched to the user's background.
3   → Generally appropriate stack but includes some unnecessary or
      mismatched technologies alongside the good choices.
1-2 → Several technology choices are clearly wrong or mismatched for
      this user's profile or target role.
0   → Technology choices are clearly inappropriate for an AI Engineer
      targeting the global market.

──────────────────────────────────────────
D4: MA — Market Alignment (Max 10)
──────────────────────────────────────────

4a. skill_demand (0-5)
QUESTION: Do the skills covered match what AI Engineer job postings
actually require in 2024-2025?

5   → Strong alignment with current market. Covers the key skills:
      Python, PyTorch or TensorFlow, LLM APIs or RAG, model deployment,
      MLOps basics, cloud platform (AWS, GCP, or Azure), vector databases
      or embedding models. Trending tools are included.
4   → Most demanded skills present. One or two important areas missing
      or underrepresented.
3   → Core skills present but misses clearly trending tools or practices
      that appear frequently in current AI Engineer job postings.
1-2 → Outdated or significantly misaligned skill set for the role.
0   → No meaningful alignment with current AI Engineer job market demands.

4b. global_alignment (0-5)
QUESTION: Will this plan make the user competitive in the global job
market including the US, EU, and remote-first companies?

5   → Clear global focus throughout. Emphasizes cloud platforms,
      internationally recognized tools and practices, GitHub presence,
      and professional communication. Skills are globally transferable.
4   → Mostly global in focus. Minor gaps in one area of global readiness.
3   → Generally globally relevant but missing key elements that matter
      for international or remote roles.
1-2 → Primarily locally focused or missing critical global market requirements.
0   → No consideration of global market demands whatsoever.

──────────────────────────────────────────
D5: SPQ — Strategic Prioritization Quality (Max 10)
──────────────────────────────────────────

5a. high_roi (0-5)
QUESTION: Does the plan focus time on the skills that most directly
lead to getting hired as an AI Engineer?

5   → Clear 80/20 focus. High-impact skills such as Python ML,
      PyTorch, model deployment, and APIs dominate the early content.
      Lower-impact or supplementary topics are compressed or deferred.
      Student time is spent where it produces the most hiring signal.
4   → Good prioritization with minor misordering. Mostly high-impact
      skills first with occasional lower-priority topic placed early.
3   → Mixed. High and low ROI topics are not clearly distinguished
      from each other. No explicit prioritization logic visible.
1-2 → Low ROI topics are given equal or greater weight than the
      high-impact skills that would actually get this user hired.
0   → No strategic prioritization evident. Topics appear in arbitrary order.

5b. progression (0-5)
QUESTION: Does the plan follow a logical learning progression from
foundational to applied to job-ready, in any format?

5   → Clear three-phase progression visible regardless of how it is
      expressed: Foundation first, then Applied Projects, then Interview
      preparation and Job Hunt. Each phase builds directly on the previous.
4   → Mostly logical progression. One phase slightly misplaced or
      overlapping awkwardly with another.
3   → General direction from basic to advanced is correct but phase
      boundaries are blurred or one phase is significantly misplaced.
1-2 → Topics appear in a roughly linear list without meaningful
      progression logic between foundation and application phases.
0   → No discernible learning progression whatsoever.

──────────────────────────────────────────
D6: CSDC — Curriculum Structural Depth & Clarity (Max 15)
──────────────────────────────────────────

6a. knowledge_progression (0-5)
QUESTION: Are topics introduced in an order where each concept builds
on previously learned material, regardless of how the plan is formatted?

5   → Strong prerequisite logic throughout the entire plan. A student
      can follow the sequence without ever encountering a concept they
      have not yet been introduced to. No topic appears before its
      foundational requirements are covered.
4   → Mostly correct ordering. One or two minor sequencing issues that
      would not significantly disrupt learning.
3   → Generally logical direction with some prerequisite violations that
      a student would need to navigate around independently.
1-2 → Significant ordering problems. Several topics introduced before
      their prerequisites. Student would be regularly confused.
0   → No logical ordering evident. Topics appear in arbitrary sequence.

6b. content_specificity (0-5)
QUESTION: Is the content specific enough that a student knows exactly
what to learn, or is it just a list of topic names and categories?

5   → Subtopics and content are specific enough to be directly actionable.
      Student knows what specific tool, concept, or skill to study next.
      For example: "model serving with FastAPI" rather than just "deployment."
4   → Good specificity overall. A few areas remain vague but most content
      is specific enough to act on.
3   → Mixed specificity. Some sections are concrete and actionable, others
      are just high-level category names that need further research.
1-2 → Mostly high-level topic names only. Student would need to research
      what to actually study within each named topic.
0   → No specificity at all. Just a list of subject area names.

6c. actionability (0-5)
QUESTION: After reading this plan, does a student know what they should
be able to DO at each stage, not just what topics to study?

5   → Clear, observable deliverables or outcomes are specified throughout.
      Student knows what they will be able to build, demonstrate, or
      perform after each major section. Outcomes are active, not passive.
4   → Good actionable outcomes in most sections. A few sections describe
      topics to study without specifying what the student can do with them.
3   → Mixed. Some sections are action-oriented with deliverables, others
      are purely topic-based with passive learning objectives.
1-2 → Mostly passive throughout. Language like "understand X" or "learn
      about Y" without specifying what the student can actually do.
0   → No outcomes or deliverables specified anywhere in the plan.

──────────────────────────────────────────
D7: CER — Career Execution Readiness (Max 10)
──────────────────────────────────────────

7a. resume (0-4)
QUESTION: Does the plan prepare the user to present themselves
effectively to employers through resume and professional presence?

4   → Resume AND LinkedIn guidance both included with meaningful content.
      ATS keyword awareness mentioned. Timing or phase for this work
      is indicated somewhere in the plan.
3   → Resume and LinkedIn both covered with useful guidance, but one
      area is lighter or timing is not indicated.
2   → Resume mentioned with some actionable guidance. LinkedIn entirely
      absent from the plan.
1   → Passing mention of resume only. No actionable guidance provided.
0   → No resume or professional presence guidance of any kind.

7b. mock_interviews (0-3)
QUESTION: Does the plan include actual interview practice mechanisms,
not just preparation content?

3   → Interview practice is specified with enough detail to be actionable.
      Platforms, format, timing, or type of practice is mentioned in any form.
2   → Mock interviews are mentioned as something the student should do
      but without any specification of how, when, or where.
1   → Interview practice is implied somewhere in the plan but never
      explicitly stated as a component.
0   → No interview practice component of any kind.

7c. application_strategy (0-3)
QUESTION: Does the plan give the user a strategy for actually getting
interviews and job offers, beyond just saying "apply for jobs"?

3   → Meaningful job search strategy is included in some form.
      Could include: networking, LinkedIn outreach, target company research,
      application volume targets, referrals, or cold outreach approach.
2   → Some application guidance is present but missing key strategic
      elements. More than generic advice but not a complete strategy.
1   → Generic advice only, such as "start applying in the last month"
      or "look for jobs online" without strategic substance.
0   → No application strategy of any kind.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — SCORING PROCESS (Follow Exactly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Read the entire learning plan carefully from start to finish.
Step 2: Check each penalty condition (Section 4).
        Note which penalties apply based on entirely absent components.
Step 3: Score each subcriterion using the QUESTION framing.
        Focus on what the plan achieves in substance, not how it looks.
        Apply penalty caps to relevant subcriteria where applicable.
Step 4: Sum subcriteria scores to get each dimension total.
        Verify: breakdown sum exactly equals dimension score.
Step 5: Sum all seven dimension scores to get Total_Score.
        Verify: sum of all seven dimensions exactly equals Total_Score.
Step 6: Write a 3-4 sentence overall_summary that covers:
        (a) Which penalties were applied and why.
        (b) The two strongest dimensions and why they scored well.
        (c) The two weakest dimensions and what was missing.
        (d) The score band this plan falls in.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 7 — REQUIRED JSON OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY the JSON below. No text before or after it.

{{
  "penalties_applied": ["List each penalty code that was applied, e.g. P1, P3. Empty list if none."],
  "HRO":  {{"score": 0, "breakdown": {{"core_technical": 0, "interview_prep": 0, "portfolio": 0}}, "comment": "1-2 sentences justifying this dimension score based on plan substance"}},
  "TCF":  {{"score": 0, "breakdown": {{"feasibility": 0, "cognitive_load": 0, "appropriateness": 0}}, "comment": ""}},
  "PPA":  {{"score": 0, "breakdown": {{"experience_adaptation": 0, "preference_integration": 0, "stack_relevance": 0}}, "comment": ""}},
  "MA":   {{"score": 0, "breakdown": {{"skill_demand": 0, "global_alignment": 0}}, "comment": ""}},
  "SPQ":  {{"score": 0, "breakdown": {{"high_roi": 0, "progression": 0}}, "comment": ""}},
  "CSDC": {{"score": 0, "breakdown": {{"knowledge_progression": 0, "content_specificity": 0, "actionability": 0}}, "comment": ""}},
  "CER":  {{"score": 0, "breakdown": {{"resume": 0, "mock_interviews": 0, "application_strategy": 0}}, "comment": ""}},
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
        plan=json.dumps(plan, indent=2)
    )

    for attempt in range(max_retries):
        try:
            print(f"  [{plan_label}] API call — attempt {attempt + 1} of {max_retries}...")

            # Anthropic API format (without assistant prefill)
            response = client.messages.create(
                model=MODEL,
                temperature=TEMPERATURE,
                max_tokens=4096,
                system=SYSTEM_MESSAGE,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Get the raw text
            raw_text = response.content[0].text
            
            # Clean up potential markdown formatting (e.g., ```json ... ```)
            raw_text = raw_text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            raw_text = raw_text.strip()
            
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
            print(f"  Raw output was:\n{raw_text[:200]}...") # Print a snippet to help debug
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
    print("HROP AI EVALUATION — Claude Independent Scoring")
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
                # Updated to Anthropic's token usage object schema
                "plan1_prompt_tokens":     response_1.usage.input_tokens,
                "plan1_completion_tokens": response_1.usage.output_tokens,
                "plan2_prompt_tokens":     response_2.usage.input_tokens,
                "plan2_completion_tokens": response_2.usage.output_tokens,
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
    output_file = "evaluation_result_claude_v3.json"
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