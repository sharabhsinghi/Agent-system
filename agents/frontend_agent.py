"""
Frontend Agent
==============
Implements Next.js pages, React components, and UI based on the product
plan and backend APIs built in this iteration.
"""

import json
from agents.base_agent import BaseAgent
from context.context_store import ContextStore


SYSTEM_PROMPT = """
You are a senior frontend engineer specialising in Next.js 14+ (App Router),
React, TypeScript, and Tailwind CSS.

You are building the UI for a rental marketplace. Your job each iteration:
1. Review the planned features and UX notes from the Product agent.
2. Review existing components and pages.
3. Write production-quality React components and Next.js pages.

Rules:
- Use Next.js App Router (app/ directory), TypeScript, Tailwind CSS.
- Write complete components — no placeholder TODOs.
- Use React Server Components where appropriate; 'use client' only when needed
  (event handlers, hooks, browser APIs).
- Handle loading and error states.
- Make components accessible (proper aria labels, semantic HTML).
- Use the project's existing component library / design patterns where visible.
- For forms: use react-hook-form + Zod for validation if the project uses it,
  otherwise use controlled components.
- For data fetching: use server components for initial data, SWR or React Query
  for client-side mutations if already in the project.
- Think rental marketplace UI: listing cards, booking calendars, search bars,
  filters, image galleries, price displays, availability pickers, review stars,
  host/guest profile cards, message threads.

Output format: a JSON object where keys are file paths (relative to repo root)
and values are the complete file content as strings.
"""


class FrontendAgent(BaseAgent):
    def __init__(self):
        super().__init__("Frontend")

    def implement(
        self,
        features: list,
        backend_files: dict,
        key_files: str,
        context: ContextStore,
    ) -> dict:
        print("\n🎨  [Frontend Agent] Building components and pages...")

        context_summary = context.summary_for_agents()
        features_json = json.dumps(features, indent=2)
        backend_summary = "\n".join(
            f"- {path}" for path in backend_files.keys()
        )

        user_prompt = f"""
{context_summary}

FEATURES AND UX NOTES:
{features_json}

BACKEND FILES CREATED THIS ITERATION (match these APIs):
{backend_summary}

EXISTING KEY FILES (match existing patterns and components):
{key_files}

Write the frontend implementation. Respond with a JSON object where:
- Keys are file paths relative to the repo root (e.g. "app/listings/page.tsx")
- Values are the complete file content as a string

Include:
1. New pages (app/.../page.tsx)
2. New components (components/... or app/.../components/...)
3. Any layout updates needed
4. Loading skeletons (loading.tsx) for new pages
5. Error boundaries (error.tsx) for new pages where needed

Aim for 4–8 files per iteration. Write complete, production-quality TypeScript + Tailwind.
Focus on the features planned — don't rewrite existing pages.
"""

        files = self.call_json(SYSTEM_PROMPT, user_prompt, max_tokens=4096)

        context.add_decision("Frontend", f"Built {len(files)} UI files: {', '.join(list(files.keys())[:5])}")

        return files  # {filepath: content}

    def revise(
        self,
        original_files: dict,
        feedback: list,
        context: ContextStore,
    ) -> dict:
        """
        Revise frontend files in response to code-review feedback.
        Returns the full set of frontend files (original merged with fixes).
        """
        print("\n🎨  [Frontend Agent] Revising files based on code review feedback...")

        context_summary = context.summary_for_agents()
        feedback_json = json.dumps(feedback, indent=2)
        original_code = "\n\n".join(
            f"// FILE: {path}\n{content}"
            for path, content in original_files.items()
        )

        user_prompt = f"""
{context_summary}

ORIGINAL FRONTEND FILES:
{original_code}

CODE REVIEW FEEDBACK (address every issue listed):
{feedback_json}

Fix all issues identified in the feedback above.
Respond with a JSON object where keys are file paths and values are the complete,
updated file content — the same format as the original implementation.
Only include files that required changes; unchanged files can be omitted.
"""

        revised = self.call_json(SYSTEM_PROMPT, user_prompt, max_tokens=4096)

        context.add_decision(
            "Frontend",
            f"Revised {len(revised)} file(s) after code review: {', '.join(list(revised.keys())[:5])}",
        )

        # Merge: start from originals, overwrite with revised versions
        return {**original_files, **revised}
