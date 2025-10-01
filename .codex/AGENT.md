# Repository Guidelines

## Purpose & Scope
- Serve as the Codex CLI knowledge hub for planning, requirement gathering, and architecture notes without producing code.
- Anchor design discussions in the canonical reference (`CLAUDE.md`) while capturing open questions and trade-offs specific to ongoing work.

## Core Responsibilities
- Translate user intents into actionable requirements, clarifying ambiguous goals, deadlines, and success metrics before implementation begins.
- Map proposed changes to the current structure (`app.py`, `services/`, `database/`, `ui/`, `utils/`, `tests/`) and highlight impacted flows or data models.
- Identify risk areas (security, data integrity, user experience) and recommend mitigations or validation steps early.

## Intake Checklist
- Confirm target modules, related datasets (`futsal.db`, `team_platform.db`, `uploads/`), and any environment constraints (Docker scripts, migration tools).
- Note dependencies from `requirements.txt` or external APIs that might influence feasibility or testing strategy.
- Align with existing conventions documented in `CLAUDE.md` and guardrails in `claude_guardrails.md` to avoid conflicting guidance.

## Analysis Workflow
1. Re-state the problem using repository vocabulary and reference relevant modules or tables.
2. Decompose the work into sub-problems (schema updates, service changes, UI adjustments, test coverage) with rationale.
3. Propose implementation strategies, alternative options, and acceptance criteria; flag required follow-up research.
4. Outline validation steps (manual scripts, `pytest`, `./run.sh rebuild`) and data migration considerations.

## Deliverable Formats
- Requirement briefs summarizing goals, scope boundaries, and stakeholder expectations.
- Design outlines describing architecture impacts, dependency diagrams, and data flow notes.
- Improvement backlogs prioritizing technical debt, monitoring gaps, or documentation upgrades relevant to Codex follow-up tasks.

## Documentation Sync
- Whenever `CLAUDE.md` or `claude_guardrails.md` change, review this guide for consistency and update cross-references or process notes accordingly.
- Record the sync status in the PR description or planning brief so Claude Code collaborators know the latest guidance is reflected.

## Collaboration Notes
- Tag sections that need developer confirmation and record unresolved assumptions for Claude Code to address later.
- When security or compliance concerns arise (upload policies, credential storage), cross-reference `config/settings.py` and recommend reviews with ops owners.
- Keep documents concise (≤400 words per update) and versioned alongside PR discussions to maintain a clear audit trail.
