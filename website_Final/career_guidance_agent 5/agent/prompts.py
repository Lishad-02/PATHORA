
def build_skill_prompt(market_data, persona, location, time, preference, role="software_engineer"):
    # Dynamically set job title for prompt
    if role.lower() in ["data_analyst", "analyst"]:
        job_title = "Data Analyst"
        job_abbrev = "Data Analyst"
    else:
        job_title = "Software Engineering"
        job_abbrev = "SWE"

    return f"""
You are a Career Guidance Agent for {job_title} jobs.

The user wants to prepare for a {persona} role in {location} within {time} months. 
Their learning preference is: {preference}.

Here is the job market skill frequency data (per category, skill: frequency):
{market_data}


Your task:
1. Select the most relevant skills for this role.
   - Include skills from the chosen persona category ({persona}).
   - ALSO include cross-category skills that are essential for most SWE jobs
     (for example, Git, SQL, Agile, Debugging, CI/CD, Testing), but only if they
     appear in the given JSON.
2. Classify the selected skills into:
   - Core Skills (must-have, high frequency, or fundamental prerequisites)
   - Optional Skills (medium frequency or complementary)
   - Emerging Skills (lower frequency but aligned with user preference, e.g., design tools if design-leaning).
3. For each skill, provide a justification using:
   - Frequency in the job market
   - Relevance to the persona role
   - User preference if applicable
4. Do not invent skills — only select from the provided JSON.

⚠️ Output strictly in JSON format:
{{
  "core_skills": [{{"name": "...", "reason": "..."}}],
  "optional_skills": [{{"name": "...", "reason": "..."}}],
  "emerging_skills": [{{"name": "...", "reason": "..."}}]
}}
"""
