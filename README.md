# 🏠 Rental Marketplace — AI Agent System

An iterative, human-in-the-loop AI agent pipeline for building your rental marketplace.
Powered by Claude (Anthropic). Built for Next.js + PostgreSQL projects.

## How it works

Each time you run the orchestrator, five agents execute in sequence:

```
Your Feedback
     ↓
[Product Agent]   → Decides features & UX for this iteration
     ↓
[Schema Agent]    → Designs/updates PostgreSQL schema
     ↓
[Backend Agent]   → Writes Next.js API routes & server actions
     ↓
[Frontend Agent]  → Builds React components & pages
     ↓
[QA Agent]        → Writes tests & flags security issues
     ↓
Files written to your repo
```

All decisions are stored in `context/project_context.json` so each iteration builds on the last.

---

## Setup

### 1. Install dependencies

```bash
cd rental-agent-system
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run your first iteration

```bash
python orchestrator.py --repo /path/to/your/nextjs/project
```

That's it. The agents will scan your codebase and propose the most logical next features.

---

## Running subsequent iterations

After reviewing the output and testing manually, give feedback:

```bash
python orchestrator.py \
  --repo /path/to/your/nextjs/project \
  --feedback "The listing page looks good but the booking form needs a date range picker, and we're missing availability blocking when a booking is confirmed."
```

Your feedback can be anything:
- Bug reports: `"The price calculation doesn't account for the cleaning fee"`
- New features: `"Add a messaging system between hosts and guests"`
- UX changes: `"The search filters need to include pet-friendly and pool options"`
- Refactors: `"The auth logic is duplicated in 3 routes, consolidate it"`

---

## What gets written to your repo

After each iteration, you'll find:

| Path | What it is |
|------|-----------|
| `migrations/001_iteration_1.sql` | SQL migration to run against your DB |
| `migrations/001_prisma_additions.prisma` | Prisma models to add to your schema.prisma |
| `app/api/.../route.ts` | New API routes |
| `app/.../page.tsx` | New pages |
| `components/...` | New components |
| `__tests__/...` | Test files |
| `migrations/001_security_report.md` | Security issues (if any) |

**Always review before committing.** The agents are good but you are the final reviewer.

---

## Recommended workflow

```
Iteration N:
  1. python orchestrator.py --repo . --feedback "..."
  2. Review the files in your editor
  3. Apply the SQL migration
  4. Update prisma/schema.prisma
  5. Run: npm run dev
  6. Test the new features manually
  7. Fix anything obvious yourself
  8. Go to Iteration N+1
```

---

## Flags

| Flag | Description |
|------|-------------|
| `--repo` | Path to your Next.js repo (required) |
| `--feedback` | Your feedback for this iteration (optional on first run) |
| `--context-file` | Path to context JSON (default: context/project_context.json) |
| `--dry-run` | Preview the plan without writing any files |

---

## Context file

`context/project_context.json` is the system's memory. It stores:
- All features (planned, in-progress, done)
- Database schema decisions
- Every agent decision, per iteration
- Full iteration history

**Commit this file to your repo** so the context persists across machines.

---

## Project structure

```
rental-agent-system/
├── orchestrator.py          ← Entry point — run this
├── requirements.txt
├── README.md
├── agents/
│   ├── orchestrator_agent.py   ← Coordinates the pipeline
│   ├── product_agent.py        ← Features & UX planning
│   ├── schema_agent.py         ← PostgreSQL schema design
│   ├── backend_agent.py        ← API routes & server logic
│   ├── frontend_agent.py       ← React components & pages
│   └── qa_agent.py             ← Tests & security review
├── tools/
│   └── repo_tools.py           ← Reads & writes your repo
└── context/
    ├── context_store.py        ← Persistent memory layer
    └── project_context.json    ← Auto-generated, commit this
```
