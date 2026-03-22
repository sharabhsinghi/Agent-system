"""
Orchestrator Agent
==================
Coordinates the full agent pipeline for one iteration.
Reads the repo, runs agents in sequence, writes output files.
"""

import json
from pathlib import Path

from agents.product_agent import ProductAgent
from agents.schema_agent import SchemaAgent
from agents.backend_agent import BackendAgent
from agents.frontend_agent import FrontendAgent
from agents.code_review_agent import CodeReviewAgent
from agents.qa_agent import QAAgent
from context.context_store import ContextStore
from tools.repo_tools import RepoTools


class OrchestratorAgent:
    def __init__(self, repo_tools: RepoTools, context_store: ContextStore, dry_run: bool = False):
        self.repo = repo_tools
        self.context = context_store
        self.dry_run = dry_run

        self.product = ProductAgent()
        self.schema = SchemaAgent()
        self.backend = BackendAgent()
        self.frontend = FrontendAgent()
        self.code_review = CodeReviewAgent()
        self.qa = QAAgent()

    def run_iteration(self, feedback: str = ""):
        iteration_num = self.context.increment_iteration()
        print(f"\n🔄  Starting Iteration #{iteration_num}")
        print("-" * 50)

        # ── Step 1: Read the repo ──────────────────────────────────────────
        print("\n📂  Scanning repository...")
        repo_structure = self.repo.scan_structure()
        key_files = self.repo.read_key_files()
        existing_schema = self.repo.read_file("prisma/schema.prisma") or \
                          self.repo.read_file("schema.sql") or ""

        print(f"  ✓  Repo structure scanned ({len(repo_structure.splitlines())} entries)")
        print(f"  ✓  Key files read ({len(key_files)} chars)")

        # ── Step 2: Product Agent ──────────────────────────────────────────
        product_plan = self.product.plan_iteration(
            repo_structure=repo_structure,
            key_files=key_files,
            context=self.context,
            feedback=feedback,
        )
        features = product_plan.get("features", [])
        self._print_plan(product_plan)

        # ── Step 3: Schema Agent ───────────────────────────────────────────
        schema_result = self.schema.design_schema(
            features=features,
            context=self.context,
            existing_schema=existing_schema,
        )

        # ── Step 4: Backend Agent ──────────────────────────────────────────
        backend_files = self.backend.implement(
            features=features,
            schema_result=schema_result,
            key_files=key_files,
            context=self.context,
        )

        # ── Step 5: Frontend Agent ─────────────────────────────────────────
        frontend_files = self.frontend.implement(
            features=features,
            backend_files=backend_files,
            key_files=key_files,
            context=self.context,
        )

        # ── Step 6: Code Review ────────────────────────────────────────────
        review_result = self.code_review.review(
            backend_files=backend_files,
            frontend_files=frontend_files,
            features=features,
            context=self.context,
        )

        # ── Step 6b: One-shot revision pass ───────────────────────────────
        # Each agent revises its own files exactly once; no second review loop.
        if review_result.get("has_issues"):
            backend_feedback = review_result.get("backend_feedback", [])
            frontend_feedback = review_result.get("frontend_feedback", [])

            if backend_feedback:
                backend_files = self.backend.revise(
                    original_files=backend_files,
                    feedback=backend_feedback,
                    context=self.context,
                )

            if frontend_feedback:
                frontend_files = self.frontend.revise(
                    original_files=frontend_files,
                    feedback=frontend_feedback,
                    context=self.context,
                )

        # ── Step 7: QA Agent ───────────────────────────────────────────────
        qa_result = self.qa.review_and_test(
            backend_files=backend_files,
            frontend_files=frontend_files,
            features=features,
            context=self.context,
        )

        # ── Step 8: Write all files ────────────────────────────────────────
        self._write_output(schema_result, backend_files, frontend_files, qa_result, iteration_num)

        # ── Step 9: Save iteration summary ────────────────────────────────
        self.context.add_iteration({
            "goal": product_plan.get("iteration_goal", ""),
            "features": [f["id"] for f in features],
            "files_written": list(backend_files.keys()) + list(frontend_files.keys()),
            "security_issues": len(qa_result.get("security_issues", [])),
        })

        self._print_summary(product_plan, backend_files, frontend_files, review_result, qa_result)

    def _write_output(self, schema_result, backend_files, frontend_files, qa_result, iteration_num):
        if self.dry_run:
            print("\n🔍  DRY RUN — no files written")
            return

        print("\n💾  Writing files...")

        # Write migration SQL
        sql = schema_result.get("sql_migration", "")
        if sql:
            migration_path = f"migrations/{iteration_num:03d}_iteration_{iteration_num}.sql"
            self.repo.write_file(migration_path, sql)

        # Write prisma schema additions (appended to a staging file for human review)
        prisma = schema_result.get("prisma_models", "")
        if prisma:
            self.repo.write_file(
                f"migrations/{iteration_num:03d}_prisma_additions.prisma",
                f"// Add these models to your prisma/schema.prisma\n\n{prisma}"
            )

        # Write backend files
        self.repo.write_files(backend_files)

        # Write frontend files
        self.repo.write_files(frontend_files)

        # Write test files
        test_files = qa_result.get("test_files", {})
        self.repo.write_files(test_files)

        # Write security report
        issues = qa_result.get("security_issues", [])
        if issues:
            report = self._format_security_report(issues, qa_result.get("qa_notes", ""))
            self.repo.write_file(
                f"migrations/{iteration_num:03d}_security_report.md",
                report
            )

    def _format_security_report(self, issues: list, notes: str) -> str:
        lines = ["# Security Review\n", f"{notes}\n\n## Issues Found\n"]
        for issue in issues:
            sev = issue.get("severity", "?").upper()
            lines.append(f"### [{sev}] {issue.get('location', '')}")
            lines.append(f"**Issue:** {issue.get('description', '')}")
            lines.append(f"**Fix:** {issue.get('recommendation', '')}\n")
        return "\n".join(lines)

    def _print_plan(self, plan: dict):
        print(f"\n🎯  Goal: {plan.get('iteration_goal', '')}")
        features = plan.get("features", [])
        print(f"📌  Features this iteration ({len(features)}):")
        for f in features:
            priority = f.get("priority", "")
            print(f"    [{priority.upper()}] {f.get('name')}: {f.get('description', '')[:80]}")
        if plan.get("out_of_scope"):
            print(f"🚫  Out of scope: {', '.join(plan['out_of_scope'])}")

    def _print_summary(self, product_plan, backend_files, frontend_files, review_result, qa_result):
        all_files = list(backend_files.keys()) + list(frontend_files.keys())
        issues = qa_result.get("security_issues", [])
        high_issues = [i for i in issues if i.get("severity") == "high"]
        review_backend_flags = len(review_result.get("backend_feedback", []))
        review_frontend_flags = len(review_result.get("frontend_feedback", []))
        revised = review_result.get("has_issues", False)

        print("\n" + "=" * 50)
        print("📊  ITERATION SUMMARY")
        print("=" * 50)
        print(f"  Files written:       {len(all_files)}")
        print(f"  Backend files:       {len(backend_files)}")
        print(f"  Frontend files:      {len(frontend_files)}")
        print(f"  Code review:         {'revised (' + str(review_backend_flags) + ' backend, ' + str(review_frontend_flags) + ' frontend flagged)' if revised else 'clean — no revision needed'}")
        print(f"  Test files:          {len(qa_result.get('test_files', {}))}")
        print(f"  Security issues:     {len(issues)} ({len(high_issues)} high)")

        if high_issues:
            print("\n  ⚠️  HIGH SEVERITY ISSUES:")
            for i in high_issues:
                print(f"     - {i.get('location')}: {i.get('description', '')[:80]}")

        print("\n  📁  Files written:")
        for f in all_files[:10]:
            print(f"     {f}")
        if len(all_files) > 10:
            print(f"     ... and {len(all_files) - 10} more")

        print("\n  Next steps:")
        print("  1. Review the files above in your editor")
        print("  2. Apply the SQL migration to your database")
        print("  3. Update prisma/schema.prisma with the generated additions")
        print("  4. Run your dev server and test manually")
        print("  5. Run: python orchestrator.py --repo . --feedback 'your feedback here'")
