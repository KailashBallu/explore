# CLAUDE.md

## Branch Strategy
- Always create a feature branch for new work — never commit directly to master.
- Branch names should be short and descriptive, using kebab-case (e.g., `add-auth-middleware`, `fix-race-condition`).

## Commit Rules
- Never include "Co-Authored-By: Claude" or similar credits in commit messages.

## Progress Tracking
- Each project has a `PROGRESS.md` that is the authoritative source of truth for development status.
- Update `PROGRESS.md` whenever a phase, task, or significant deliverable is completed.
- `PROGRESS.md` should be structured so any developer or coding agent can read it cold and resume work.
