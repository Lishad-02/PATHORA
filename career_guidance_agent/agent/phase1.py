from .loader import load_market_data
from .prompts import build_skill_prompt
from .llm_factory import call_llm
from .verifier import verify_output


def run_phase1(location, persona, time, preference, provider="openai", role="software_engineer"):
    """
    Executes Phase 1 (Skill Recommendation)
    """
    # Pass persona into loader (so it can choose specialized data later)
    data = load_market_data(location, role, persona)

    # Build prompt using the selected persona specialization
    prompt = build_skill_prompt(data, persona, location, time, preference)

    # Call chosen LLM provider
    raw_output = call_llm(prompt, provider=provider, temperature=0)

    # Verify output
    final_output = verify_output(raw_output, data)

    return final_output
