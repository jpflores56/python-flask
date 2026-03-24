# Contributing to python-flask

Thank you for your interest in contributing to this project. This repository is a **sandbox for testing AI-assisted development workflows**, not a production system. All contributions must be small, auditable, and reversible.

This guide synthesizes governance rules from [`mcp.md`](mcp.md) with project-specific context. Please read it fully before submitting changes.

---

## Pull Request Process

### One Task Per PR

Each pull request must address **one logical task only**. Do not combine unrelated changes, cross-domain refactors, or multi-feature work into a single PR.

### Change Size Limits

- Changes must remain **under 200 lines per PR**
- No large-scale rewrites
- Refactors must preserve existing behavior

### Branch Naming

- Always create a **new branch per task**
- Branch names **must reference the task intent** (e.g., `fix/add-user-validation`, `feat/gol-42-auth-endpoint`)

### PR Requirements

Every pull request **must** include:

1. **Summary of changes** — What changed and why
2. **Risk assessment** — What could go wrong
3. **Rollback plan** — How to revert if needed
4. **How to test it** — Steps to verify the change
5. **Potential side effects** — Anything else affected

### Review and Approval

All write, commit, and push actions **require human approval**. AI agents must never assume approval. A maintainer must review and approve every PR before it is merged.

---

## Scope Rules

- **No cross-domain refactors** unless explicitly requested
- **No renaming directories** without approval
- **No restructuring project layout**
- Changes should be focused and minimal

---

## Testing Requirements

- **All code changes must include corresponding tests**
- No removal of tests without explicit approval
- Existing tests must continue to pass
- See the [Testing Guide](docs/guides/testing.md) for conventions and how to run the test suite

---

## Safety Guardrails

Contributors (including AI agents) must **NOT**:

- Modify configuration outside this repository
- Introduce new external dependencies
- Modify deployment or infrastructure files
- Access secrets or environment variables

---

## Reproducibility

- All tasks must be **executable via CLI**
- No manual IDE-only steps allowed
- All changes must be **reproducible from a clean clone**

---

## Failure Protocol

If you are uncertain about a change:

1. **Stop** — Do not proceed
2. **Ask for clarification** — Open an issue or comment on the task
3. **Do not guess intent** — Ambiguity must be resolved before implementation

---

## ⚠️ Educational Bugs — Do Not Fix Without Approval

This project **intentionally contains 7 bugs** for educational and testing purposes. These bugs exist to help learners practice debugging and to test AI-assisted development workflows.

The intentional bugs include:

1. **SQL injection vulnerability** — Unsanitized database queries
2. **Memory leaks** — Resources not properly released
3. **Missing input validation** — Endpoints accepting invalid data
4. **Missing 404 handling** — Routes that don't return proper not-found responses
5. **Code duplication** — Repeated logic that should be consolidated
6. **Hard-coded configuration** — Values that should be externalized
7. **Failing tests** — Tests that are intentionally broken

### Rules for Educational Bugs

- **Do NOT fix these bugs** unless explicitly requested as a specific task
- AI agents must **not "improve" or "clean up"** these bugs without approval
- If you encounter one of these bugs during other work, **leave it as-is** and note its presence
- Fixing an educational bug without approval violates the contribution policy

---

## Documentation

For more information about the project, refer to these guides in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture/overview.md) | System architecture and design decisions |
| [Getting Started Guide](docs/guides/getting-started.md) | Setup, installation, and first steps |
| [Testing Guide](docs/guides/testing.md) | Testing conventions, running tests, writing tests |
| [API Reference](docs/api/endpoints.md) | API endpoint documentation |
| [Coding Conventions](docs/CONVENTIONS.md) | Code style and project conventions |
| [MCP Governance Policy](mcp.md) | Full governance rules for AI-assisted workflows |

---

## Governance Reference

This contributing guide is derived from the [MCP Governance Policy](mcp.md). When in doubt, `mcp.md` is the authoritative source for governance rules. The key principles are:

- This repository exists to test AI-assisted development workflows safely
- All changes must be small, auditable, and reversible
- This is not a production system
- Human approval is required for all modifications
