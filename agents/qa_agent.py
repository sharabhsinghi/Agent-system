"""
QA & Security Agent
===================
Reviews the code produced this iteration and writes tests.
Also flags security concerns for the rental marketplace context.
"""

import json
from agents.base_agent import BaseAgent
from context.context_store import ContextStore


SYSTEM_PROMPT = """
You are a senior QA engineer and security reviewer specialising in Next.js,
TypeScript, and PostgreSQL applications — specifically rental marketplace apps.

Your job each iteration:
1. Review the backend and frontend code produced.
2. Write meaningful tests (unit + integration where possible).
3. Flag any security issues specific to a rental marketplace.

Testing rules:
- Use Jest + React Testing Library for component tests.
- Use Jest for API route/utility unit tests.
- Write tests that actually test behaviour, not implementation details.
- Cover happy paths AND error cases.
- Mock Supabase/DB calls appropriately.

Security checklist for rental marketplaces:
- Auth on every protected route/action (guests can't modify other users' listings)
- Input validation (SQL injection, XSS, price manipulation)
- Booking race conditions (double-booking prevention)
- File upload safety (listing images)
- Payment amount validation (never trust client-side prices)
- Rate limiting on search/booking endpoints
- PII handling (guest data, host contact info)
- RLS policies in Supabase

Output format: a JSON object with:
- "test_files": { filepath: content } — test files to write
- "security_issues": [ { severity, location, description, recommendation } ]
- "qa_notes": "Summary of what was tested and any gaps"
"""


class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__("QA")

    def review_and_test(
        self,
        backend_files: dict,
        frontend_files: dict,
        features: list,
        context: ContextStore,
    ) -> dict:
        print("\n🔒  [QA Agent] Writing tests and reviewing security...")

        context_summary = context.summary_for_agents()
        features_json = json.dumps(features, indent=2)

        # Give the QA agent the actual code to review
        all_files = {**backend_files, **frontend_files}
        code_review_input = "\n\n".join(
            f"=== {path} ===\n{content[:3000]}"
            for path, content in list(all_files.items())[:8]  # cap to avoid token limit
        )

        user_prompt = f"""
{context_summary}

FEATURES THIS ITERATION:
{features_json}

CODE TO REVIEW AND TEST:
{code_review_input}

Write tests for the most critical paths and flag any security issues.
"""

        result = self.call_json(SYSTEM_PROMPT, user_prompt, max_tokens=4096)

        # Log security issues
        issues = result.get("security_issues", [])
        if issues:
            high = [i for i in issues if i.get("severity") == "high"]
            context.add_decision("QA", f"Found {len(issues)} security issues ({len(high)} high severity)")
        else:
            context.add_decision("QA", "No security issues found this iteration")

        return result
