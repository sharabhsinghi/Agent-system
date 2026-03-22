"""
Backend Agent
=============
Implements Next.js API routes, server actions, and business logic
based on features and schema from earlier agents.
"""

import json
from agents.base_agent import BaseAgent
from context.context_store import ContextStore


SYSTEM_PROMPT = """
You are a senior full-stack engineer specialising in Next.js 14+ (App Router),
TypeScript, Supabase/PostgreSQL, and modern backend patterns.

You are building the backend for a rental marketplace. Your job each iteration:
1. Review the planned features and database schema.
2. Review the existing codebase.
3. Write production-quality API routes, server actions, and utility functions.

Rules:
- Use Next.js App Router conventions (app/api/... route handlers OR server actions).
- Use TypeScript throughout — no `any` types.
- Validate inputs with Zod.
- Handle errors gracefully — always return typed responses.
- Use Supabase client for database access (or the project's existing DB client).
- Never hardcode secrets — use environment variables.
- Write complete files, not snippets. Every file should be immediately usable.
- Include JSDoc comments on exported functions.
- Think about auth: use Supabase Auth or the project's existing auth pattern.
- For a rental marketplace: handle bookings, availability checks, listing CRUD,
  user profiles, search/filter, payment intents, reviews, messages.

Output format: a JSON object where keys are file paths (relative to repo root)
and values are the complete file content as strings.
"""


class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__("Backend")

    def implement(
        self,
        features: list,
        schema_result: dict,
        key_files: str,
        context: ContextStore,
    ) -> dict:
        print("\n⚙️   [Backend Agent] Implementing API routes and logic...")

        context_summary = context.summary_for_agents()
        features_json = json.dumps(features, indent=2)
        schema_json = json.dumps({
            "prisma_models": schema_result.get("prisma_models", ""),
            "tables": schema_result.get("new_tables", []) + schema_result.get("modified_tables", []),
        }, indent=2)

        user_prompt = f"""
{context_summary}

FEATURES TO IMPLEMENT:
{features_json}

DATABASE SCHEMA:
{schema_json}

EXISTING KEY FILES (for context — match existing patterns):
{key_files}

Write the backend implementation. Respond with a JSON object where:
- Keys are file paths relative to the repo root (e.g. "app/api/listings/route.ts")
- Values are the complete file content as a string

Include:
1. API route handlers for each feature
2. Server actions where appropriate (for form submissions)
3. Type definitions (types/index.ts additions or new type files)
4. Database utility functions (lib/ helpers)
5. Zod validation schemas

Aim for 3–6 files per iteration. Write complete, production-quality TypeScript.
Focus on the features planned for this iteration — don't rewrite existing code.
"""

        files = self.call_json(SYSTEM_PROMPT, user_prompt, max_tokens=4096)

        context.add_decision("Backend", f"Implemented {len(files)} files: {', '.join(list(files.keys())[:5])}")

        return files  # {filepath: content}

    def revise(
        self,
        original_files: dict,
        feedback: list,
        context: ContextStore,
    ) -> dict:
        """
        Revise backend files in response to code-review feedback.
        Returns the full set of backend files (original merged with fixes).
        """
        print("\n⚙️   [Backend Agent] Revising files based on code review feedback...")

        context_summary = context.summary_for_agents()
        feedback_json = json.dumps(feedback, indent=2)
        original_code = "\n\n".join(
            f"// FILE: {path}\n{content}"
            for path, content in original_files.items()
        )

        user_prompt = f"""
{context_summary}

ORIGINAL BACKEND FILES:
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
            "Backend",
            f"Revised {len(revised)} file(s) after code review: {', '.join(list(revised.keys())[:5])}",
        )

        # Merge: start from originals, overwrite with revised versions
        return {**original_files, **revised}
