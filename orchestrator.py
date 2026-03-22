#!/usr/bin/env python3
"""
Rental Marketplace — AI Agent Orchestrator
==========================================
Run an iteration:
    python orchestrator.py --repo /path/to/your/repo --feedback "Add a booking calendar"
First run (no feedback):
    python orchestrator.py --repo /path/to/your/repo
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

from agents.orchestrator_agent import OrchestratorAgent
from tools.repo_tools import RepoTools
from context.context_store import ContextStore


def main():
    parser = argparse.ArgumentParser(description="Rental Marketplace AI Agent System")
    parser.add_argument("--repo", required=True, help="Path to your local GitHub repo")
    parser.add_argument("--feedback", default="", help="Your feedback / instructions for this iteration")
    parser.add_argument("--context-file", default="context/project_context.json", help="Path to context store file")
    parser.add_argument("--dry-run", action="store_true", help="Preview plan without writing files")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"❌  Repo path not found: {repo_path}")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌  ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    print("\n🏠  Rental Marketplace Agent System")
    print("=" * 50)
    print(f"📁  Repo: {repo_path}")
    print(f"💬  Feedback: {args.feedback or '(first run — scanning codebase)'}")
    print(f"🕐  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    context_store = ContextStore(args.context_file)
    repo_tools = RepoTools(repo_path)

    orchestrator = OrchestratorAgent(
        repo_tools=repo_tools,
        context_store=context_store,
        dry_run=args.dry_run,
    )

    orchestrator.run_iteration(feedback=args.feedback)

    print("\n✅  Iteration complete!")
    print(f"📋  Context saved to: {args.context_file}")
    if not args.dry_run:
        print(f"📝  Files written to repo. Review changes, then commit when ready.")


if __name__ == "__main__":
    main()
