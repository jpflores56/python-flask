# Documentation Audit Request — Instructions Preset

> **Purpose:** This file provides instructions for the request-formulator agent to analyze a codebase and craft a project-specific Documentation Audit Epic Request. The agent must perform real analysis — the resulting Epic Request will be unique to the project.

---

> 🔴 **CRITICAL SCOPE RULE — READ BEFORE ANYTHING ELSE:**
> This audit covers **high-level documentation ONLY** — architecture docs, READMEs, guides, conventions, API docs.
> **Inline code commenting (XML docs, JSDoc, TSDoc, code-level comments) is STRICTLY EXCLUDED.**
> Do NOT include inline commenting in the analysis findings, proposed solution, goals, success metrics, features, or tasks.
> Do NOT set goals like "100% XML doc coverage" or "every public method has doc comments."
> Code commenting is a **separate follow-up epic** that happens AFTER high-level docs are complete.
> See the **Scope Boundaries** section below for full details.

---

## Analysis Instructions

Perform the following analysis using `read` and `search` tools before crafting the Epic Request.

### 1. Project Structure Analysis

- Identify the project type (monorepo, single package, microservices, etc.)
- List all packages, services, and key directories
- Identify entry points, main configuration files, and build systems
- Note the tech stack (languages, frameworks, databases, infrastructure)
- Map high-level service/package boundaries and relationships

### 2. Existing Documentation Inventory

Scan for and catalog ALL existing documentation:
- Root `README.md` and any package-level READMEs
- `docs/` folder contents and structure
- `CONTRIBUTING.md`, `CHANGELOG.md`, `CLAUDE.md`, `CONVENTIONS.md`
- `.github/copilot-instructions.md` and instruction files
- Architecture docs, API docs, deployment guides
- Any other markdown files in the repository

> ⚠️ **Inventory only (do NOT include in proposed solution):** Note the general state of inline code comments (JSDoc/TSDoc/XML doc coverage) for awareness, but do NOT propose adding or improving them. This is out of scope.

### 3. Documentation Accuracy Assessment

For each piece of existing documentation found:
- Does it reflect the ACTUAL current state of the code?
- Are file paths, function names, and API endpoints still correct?
- Are described patterns and conventions actually followed in the code?
- **Do NOT assume any existing documentation is accurate** — verify against the codebase

### 4. Gap Analysis

Identify what documentation is MISSING that would be needed for:
- **AI agents**: Patterns, conventions, architectural decisions, non-obvious behaviors, key abstractions, "gotchas", environment setup
- **Human engineers**: Onboarding, contributing, debugging, deployment, architecture understanding
- **Both**: API references, configuration guides, testing approach, error handling patterns

### 5. Convention & Pattern Discovery

- Identify actual coding conventions from the code (naming, file structure, error handling, testing patterns)
- Check if these conventions are documented anywhere
- Note discrepancies between documented and actual conventions
- Identify key architectural patterns and whether they're explained

### 6. Build/Test/Deploy Documentation

- Check if build commands are documented and accurate
- Check if test commands and testing conventions are documented
- Check if deployment processes are documented
- Check if environment setup / configuration is documented

---

## End Goal & Expectations

The documentation audit should ultimately produce documentation that enables:

1. **AI Agent Onboarding**: A new AI agent starting a session should be able to fully understand the codebase from documentation alone — without needing to explore or grep the codebase to understand basic architecture, patterns, or conventions.

2. **Engineer Onboarding**: A new engineer should be able to start contributing without relying on tribal knowledge or asking teammates for context that should be written down.

3. **SpecTree Epic Planning**: Future SpecTree epics should have complete context available so that planners can create accurate, well-scoped features and tasks.

4. **Accuracy & Trust**: All documentation should be verified against the actual codebase. No inaccuracies should remain. Documentation should be a reliable source of truth.

---

## What "Complete" Documentation Looks Like

> 🔴 **Reminder:** "Complete" documentation in this context means high-level documentation only. Inline code comments (XML docs, JSDoc, TSDoc) are NOT part of this audit and should NOT appear in goals, metrics, or proposed work.

The following documentation should exist and be accurate:

| Document | Purpose | Location |
|----------|---------|----------|
| Root README | Project overview, architecture summary, getting started | `README.md` |
| Package READMEs | Purpose, key files, patterns, APIs for each package | `packages/*/README.md` |
| Architecture Docs | System design, data flows, service boundaries, key decisions | `docs/architecture/` |
| Coding Conventions | Naming, patterns, testing, error handling, file structure | `docs/CONVENTIONS.md` or similar |
| API Documentation | Endpoints, schemas, authentication, examples | `docs/api/` |
| AI Context | Key decisions, non-obvious patterns, "gotchas", environment | `.github/copilot-instructions.md` |
| Contributing Guide | How to contribute, PR process, code review expectations | `CONTRIBUTING.md` |
| Setup / Getting Started | Environment setup, dependencies, running locally | `docs/guides/getting-started.md` |
| Deployment Guide | Deployment processes, environments, CI/CD | `docs/guides/deployment.md` |

> **Note:** Not every project needs every document. The agent should assess what's appropriate based on project size and complexity.

---

## Key Principles

1. **Verify, don't assume** — Existing documentation may be outdated, incorrect, or misleading. Always cross-reference against the actual codebase.

2. **AI-first documentation** — AI agents need different things than humans: explicit patterns, file-to-concept mappings, convention lists, architectural decision records, and "if you see X, it means Y" guidance.

3. **Organization matters** — Documentation should have a clear hierarchy, proper cross-references, and be discoverable. A pile of accurate but disorganized docs is almost as bad as no docs.

4. **Actionable over theoretical** — "The API uses Fastify with Zod validation on all routes" is better than "The API layer handles HTTP requests."

5. **Living documentation** — The structure should be maintainable. Prefer updating existing files over creating new ones when the scope overlaps.

6. **Docs directory is home** — All new documentation must be created under the `docs/` directory with appropriate subdirectories (e.g., `docs/architecture/`, `docs/guides/`, `docs/api/`). The only exceptions are standard root-level files that tools and platforms expect at the root (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/copilot-instructions.md`). Package-level READMEs (`packages/*/README.md`) are also acceptable at their respective package roots.

7. **Mermaid for all diagrams** — All diagrams, flowcharts, architecture visuals, sequence diagrams, and data flow charts must use [Mermaid](https://mermaid.js.org/) syntax embedded in markdown code blocks. Do NOT use ASCII art diagrams. Mermaid renders natively in GitHub, VS Code, and most documentation viewers.

---

## Scope Boundaries

This audit focuses on **high-level documentation only**. The following are explicitly **out of scope** for the initial audit:

### ❌ Out of Scope: Inline Code Commenting

Inline code comments (JSDoc, TSDoc, code-level documentation) are **NOT** part of this audit. Reasons:

- Large codebases can have thousands of functions — attempting to comment everything in one pass is overwhelming and produces lower-quality results.
- Code commenting is more effective **after** high-level documentation (architecture, conventions, patterns) is complete, because the agents doing the commenting will have better context about the codebase.
- Code commenting should be proposed as a **separate follow-up epic** after the high-level documentation audit is finished.

> **For the inventory step:** You should still *scan* for existing inline comments and JSDoc/TSDoc coverage to assess the current state, but the proposed solution should NOT include adding or improving inline code comments. Instead, note the state of code commenting and recommend it as a follow-up phase.

### ✅ In Scope

- Architecture documentation
- API documentation
- Setup, deployment, and getting started guides
- Coding conventions and patterns documentation
- AI agent context documentation
- README files (root and package-level)
- Contributing guides

---

## How to Craft the Epic Request

Based on YOUR analysis of THIS specific codebase, craft the Epic Request with:

### Title
`Codebase Documentation Audit & Enhancement` (or more specific if appropriate, e.g., "API Documentation Overhaul" if that's the primary gap)

### Problem Statement
Describe what you FOUND in your analysis:
- What documentation exists and what state it's in
- What's missing, outdated, or inaccurate
- Why this is a problem for AI agents and engineers specifically
- The gap between codebase reality and documentation

### Proposed Solution
Describe what work needs to happen based on YOUR findings:
- Which documents need to be created, updated, or reorganized
- What analysis/verification work is needed
- How documentation should be structured for this project
- Priority order based on impact

> 🔴 **REQUIRED:** The proposed solution MUST include an explicit **"Out of Scope"** statement that reads:
> *"Inline code commenting (XML docs, JSDoc, TSDoc, code-level comments) is explicitly excluded from this audit. Code commenting should be a separate follow-up epic after high-level documentation is complete."*
> This ensures the planner who creates the epic from this request knows what NOT to include.

### Impact Assessment
Why this matters for THIS project:
- How it will improve AI agent effectiveness
- How it will improve engineer productivity
- What risks it mitigates (stale docs, knowledge silos, AI errors)

### Success Metrics
Concrete, verifiable outcomes:
- Specific documents that should exist and be accurate
- Specific gaps that should be filled
- Measurable: "AI agent can understand X from docs alone"

> 🔴 **Do NOT** include inline code comment metrics (e.g., "100% XML doc coverage", "every public method documented"). Only include metrics for high-level documentation artifacts.

### Target Audience
- Primary: Future AI agents working on this project
- Secondary: Human engineers onboarding or contributing

### Estimated Effort
Based on the scope of gaps you found — be specific:
- Small project with decent docs: "3-5 days"
- Large project with significant gaps: "2-3 weeks"
- Massive codebase with minimal docs: "3-4 weeks"

---

## Post-Completion

When the documentation audit epic is completed (all documentation work is done), the completing agent should create the sentinel file:

**File:** `.spectree/docs-audit.json`
```json
{
  "completedAt": "<ISO-8601 timestamp>",
  "method": "spectree",
  "epicRequestId": "<uuid of the epic request>",
  "version": 1
}
```

This prevents the request-formulator from prompting for documentation audit again on future invocations.
