"""
Init Agent
==========
Runs once before the first iteration to analyse the existing codebase and
populate the context store with:
  - Project metadata (name, detected stack, description)
  - Existing DB schema (tables, columns, relationships)
  - Existing features / modules already present in the codebase
  - Key architectural decisions already visible in the code

This gives every subsequent agent a solid foundation to build on instead
of starting cold.
"""

import json
from agents.base_agent import BaseAgent
from context.context_store import ContextStore


SYSTEM_PROMPT = """
You are a senior software architect performing an initial codebase audit.
Your job is to analyse an existing repo and extract structured, factual
information that will guide an AI agent team in future development iterations.

Be accurate and concise. Only describe what is genuinely present in the code —
do not invent or assume features that are not clearly visible.

You must respond with a single JSON object — no prose, no markdown fences.
"""


class InitAgent(BaseAgent):
    def __init__(self):
        super().__init__("Init")

    def initialize(
        self,
        repo_structure: str,
        key_files: str,
        context: ContextStore,
    ) -> dict:
        """
        Analyse the codebase and write the base context.

        Returns the analysis dict and persists it to the context store.
        """
        print("\n🔎  [Init Agent] Analysing codebase to build base context...")

        user_prompt = f"""
Analyse the following codebase and return a JSON object with this exact structure:

{{
  "project": {{
    "name": "<project or app name, inferred from package.json or README>",
    "description": "<one-sentence description of what the app does>",
    "stack": "<comma-separated list of key technologies, e.g. Next.js 14, TypeScript, Supabase, Tailwind CSS, Prisma>"
  }},
  "existing_schema": {{
    "summary": "<plain-English summary of the database structure>",
    "tables": [
      {{
        "name": "<table name>",
        "columns": ["<col: type>"],
        "relationships": ["<plain-English FK description>"]
      }}
    ]
  }},
  "existing_features": [
    {{
      "id": "<snake_case_id>",
      "name": "<Feature Name>",
      "description": "<what this feature does>",
      "status": "existing",
      "priority": "high"
    }}
  ],
  "architecture_notes": [
    "<key architectural decision or pattern observed>"
  ]
}}

If a section has no information (e.g. no DB schema found), use an empty list [] or
an empty string "" rather than omitting the key.

REPO STRUCTURE:
{repo_structure}

KEY FILES:
{key_files}
"""

        analysis = self.call_json(SYSTEM_PROMPT, user_prompt, max_tokens=4096)

        # Persist to context store
        project_info = analysis.get("project", {})
        if project_info:
            context.set("project", {
                **context.get("project", {}),
                "name": project_info.get("name", "Rental Marketplace"),
                "description": project_info.get("description", ""),
                "stack": project_info.get("stack", ""),
            })

        existing_schema = analysis.get("existing_schema", {})
        if existing_schema:
            context.update_schema(existing_schema)

        existing_features = analysis.get("existing_features", [])
        if existing_features:
            context.add_features(existing_features)

        for note in analysis.get("architecture_notes", []):
            context.add_decision("Init", note)

        context.set("initialized", True)

        feature_count = len(existing_features)
        table_count = len(existing_schema.get("tables", []))
        print(f"  ✓  Found {table_count} DB table(s) and {feature_count} existing feature(s)")
        print(f"  ✓  Stack: {project_info.get('stack', 'unknown')}")
        print(f"  ✓  Base context saved — ready for iteration 1")

        return analysis
