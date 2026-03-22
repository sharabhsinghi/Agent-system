"""
Product Agent
=============
Analyses the codebase and user feedback, then decides what features to build
in this iteration and how the UX should work.
"""

from agents.base_agent import BaseAgent
from context.context_store import ContextStore
from tools.repo_tools import RepoTools


SYSTEM_PROMPT = """
You are a senior product manager specialising in rental marketplace apps (think Airbnb, 
VRBO, or equipment rental platforms). You are part of an AI agent team building a 
Next.js + PostgreSQL rental marketplace.

Your job each iteration:
1. Review the existing codebase and project context.
2. Review the user's feedback (if any).
3. Decide which features to build or improve this iteration.
4. Write clear user stories and UX notes for the implementation agents.

Rules:
- Keep each iteration focused. Pick 2–4 concrete features max.
- Always consider the existing code — don't redesign what already works.
- Be specific about UX: page names, component names, user flows, form fields.
- Think about a rental marketplace: listings, bookings, availability, payments, reviews, 
  host/guest roles, search/filter, messaging.
"""


class ProductAgent(BaseAgent):
    def __init__(self):
        super().__init__("Product")

    def plan_iteration(
        self,
        repo_structure: str,
        key_files: str,
        context: ContextStore,
        feedback: str,
    ) -> dict:
        print("\n📋  [Product Agent] Planning iteration...")

        context_summary = context.summary_for_agents()
        iteration_number = context.get("current_iteration", 1)

        user_prompt = f"""
{context_summary}

CURRENT CODEBASE STRUCTURE:
{repo_structure}

KEY FILES:
{key_files}

USER FEEDBACK FOR THIS ITERATION:
{feedback or "No specific feedback — this is the first iteration. Analyse the codebase and propose the most valuable next features for a rental marketplace MVP."}

ITERATION NUMBER: {iteration_number}

Based on all of the above, respond with a JSON object:
{{
  "iteration_goal": "One sentence describing the focus of this iteration",
  "features": [
    {{
      "id": "feature_snake_case_id",
      "name": "Feature Name",
      "description": "What this feature does and why it matters",
      "status": "planned",
      "priority": "high|medium|low",
      "user_stories": [
        "As a guest, I can ... so that ...",
        "As a host, I can ... so that ..."
      ],
      "ux_notes": {{
        "pages_affected": ["e.g. /listings, /booking/[id]"],
        "new_components": ["e.g. BookingCalendar, PriceBreakdown"],
        "user_flow": "Step-by-step description of the user interaction"
      }}
    }}
  ],
  "out_of_scope": ["Things explicitly NOT to build this iteration"],
  "product_notes": "Any important product decisions or trade-offs"
}}
"""

        result = self.call_json(SYSTEM_PROMPT, user_prompt, max_tokens=3000)

        # Persist to context store
        context.add_decision("Product", result.get("iteration_goal", ""))
        context.add_features(result.get("features", []))

        return result
