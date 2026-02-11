# MCP Governance Policy
Project: python-flask
Purpose: Sandbox for testing Claude Code + MCP workflows

---

## 1. Intent

This repository exists to test AI-assisted development workflows safely.
All changes must be small, auditable, and reversible.

This is not a production system.

---

## 2. Scope Rules

- One logical task per pull request
- No cross-domain refactors unless explicitly requested
- No renaming directories without approval
- No restructuring project layout

---

## 3. Change Size Limits

- Changes must remain under 200 lines per PR
- No large-scale rewrites
- Refactors must preserve behavior

---

## 4. Testing Requirements

- All code changes must include corresponding tests
- No removal of tests without explicit approval
- Existing tests must continue to pass

---

## 5. Safety Guardrails

The AI must NOT:

- Modify configuration outside this repository
- Introduce new external dependencies
- Modify deployment or infrastructure files
- Access secrets or environment variables

---

## 6. Git Workflow Rules

- Always create a new branch per task
- Branch name must reference task intent
- PR must include:
  - Summary of changes
  - Risk assessment
  - Rollback plan

---

## 7. Observability

Every PR must include:

- What changed
- Why it changed
- How to test it
- Potential side effects

---

## 8. Human-in-the-Loop

All write, commit, and push actions require human approval.
AI must never assume approval.

---

## 9. Reproducibility

All tasks must be executable via CLI.
No manual IDE-only steps allowed.
All changes must be reproducible from a clean clone.

---

## 10. Failure Protocol

If uncertain:
- Stop
- Ask for clarification
- Do not guess intent
