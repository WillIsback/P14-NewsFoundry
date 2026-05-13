---
title: Validate ai-devops-toolkit v0.0.2 — code-review + docgen
date: 2026-05-11
status: Approved
author: WillIsback
---

# Design — Validate ai-devops-toolkit v0.0.2

## Context

The `ai-devops-toolkit` has been rewritten from Python to Rust. Two tools are now distributed as pre-compiled binaries via GitHub Releases (`v0.0.2`):

- `code-review-cli-linux-amd64` — reviews PR diffs via vLLM and posts a comment
- `docgen-linux-amd64` — generates docstrings for Python and TypeScript files via AST + vLLM

NewsFoundry already consumes `code-review` as a GitHub Composite Action (`@main`). There is no docgen workflow in CI — docgen is a local developer tool invoked via CLI.

## Goal

Validate both tools end-to-end:
1. Pin `code-review` to `@v0.0.2` for stability
2. Test the 3 docgen invocation methods locally, on a real file without docstrings
3. Commit the generated docstrings and open a PR — which triggers the code-review action as live validation

## Branch

`feat/validate-ai-toolkit` in NewsFoundry.

## Changes

### 1. `.github/workflows/ai-code-review.yml`

Pin the action reference from `@main` to `@v0.0.2`:

```yaml
uses: WillIsback/ai-devops-toolkit/code-review@v0.0.2
```

Everything else (guardrails, self-hosted runner, secrets mapping) is unchanged.

### 2. Docgen test — target file

**Target:** `frontend/src/service/auth.dal.ts`

Business logic (data access layer) — good candidate for useful docstrings. Not auto-generated code.

**Invocation sequence** (run from `~/work/ai-devops-toolkit/`):

```bash
# 1. Download binary via postinstall
pnpm install

# 2. Direct binary
./bin/docgen /path/to/auth.dal.ts

# 3. uv shim
uv run docgen /path/to/auth.dal.ts --force

# 4. pnpm script
pnpm run docgen -- /path/to/auth.dal.ts --force
```

The generated docstrings are committed to the branch.

### 3. Pull Request

- Title: `feat: validate ai-devops-toolkit v0.0.2 — code-review + docgen`
- Triggers `ai-code-review.yml` automatically on open
- Validates that the Rust binary is downloaded from releases and the review comment is posted

## Out of scope

- No docgen CI workflow (docgen stays a local CLI tool for now)
- No changes to the toolkit repo unless a bug is found during testing
- No changes to other NewsFoundry workflows
