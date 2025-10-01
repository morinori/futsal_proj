# Claude Code Guardrails

## Overview
- Use this document to track coding standards, security rules, and mandatory checks for implementation tasks.

## Must-Follow Rules
- Document linting, formatting, and testing requirements before merging.
- Capture prohibited patterns (hard-coded secrets, unsafe file access, unchecked user input).
- Reference `CLAUDE.md` for architectural context and update both files when guardrails change.

## Deployment References
- Consult `run.sh` before touching runtime flow; its Docker commands (`start`, `restart`, `rebuild`, volume mounts) define the supported lifecycle.
- Mirror dependency or build changes in `Dockerfile` and confirm `run.sh` still succeeds; avoid introducing docker compose unless `ops/` workflow is explicitly refactored for it.
- Do not add `docker-compose.yml` or compose-specific scripts in this repo unless the ops owner approves a migration plan documented in `docs/RFCs/`.
- Review `futsal.nginx.conf` when altering media paths or static routing to keep Nginx and app expectations aligned.

## Review Workflow
- Update this guardrail list whenever tooling or policies shift.
- Require acknowledgement in pull requests that these rules were applied.
