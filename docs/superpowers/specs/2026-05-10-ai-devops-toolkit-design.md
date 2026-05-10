# Design Spec — ai-devops-toolkit (Composite Action)

**Date:** 2026-05-10  
**Status:** Approved  
**Author:** WillIsback

---

## Problem

The AI code review script (`scripts/ai_code_reviewer.py`) is embedded directly in NewsFoundry. Every new project (P12, P13, P14...) that wants the same review must copy-paste the script and maintain it independently. A change to the prompt or the model configuration requires updating N repositories.

## Goal

Extract the review script into a standalone, centralized repository (`WillIsback/ai-devops-toolkit`) exposed as a GitHub Composite Action. Any project can call it with a single `uses:` line. One change in the toolkit repo propagates to all consumers.

---

## Architecture

### New repository: `ai-devops-toolkit`

Created locally at `/home/will/work/ai-devops-toolkit/`, to be pushed to GitHub as `WillIsback/ai-devops-toolkit` (public).

```
ai-devops-toolkit/
├── code-review/
│   ├── action.yml        ← Composite Action definition
│   └── reviewer.py       ← Python script (moved from NewsFoundry/scripts/)
└── README.md
```

### `code-review/action.yml`

Declares the Composite Action with the following inputs:

| Input | Required | Default | Description |
|---|---|---|---|
| `vllm-url` | yes | — | Base URL of the vLLM server (e.g. `http://192.168.1.87:30000/v1`) |
| `github-token` | yes | — | GitHub token for API calls and posting comments |
| `vllm-model` | no | `""` | Override model ID (auto-detected if empty) |
| `vllm-timeout` | no | `120` | Total request timeout in seconds |
| `vllm-retries` | no | `2` | Number of retries on failure |

Steps inside the action:
1. Install Python dependencies (`openai`, `httpx`, `requests`)
2. Validate that `vllm-url` is non-empty
3. Run `reviewer.py` with all inputs mapped to env vars

### `code-review/reviewer.py`

Moved verbatim from `NewsFoundry/scripts/ai_code_reviewer.py`. No logic changes. Reads configuration from environment variables already set by `action.yml`.

---

## Consumer side — NewsFoundry workflow

`NewsFoundry/.github/workflows/ai-code-review.yml` is simplified to remove the inline script management steps. What remains:

- `on: pull_request` trigger with path filters
- `permissions` block
- Guardrail job (`ai-review-skipped`) for external PRs — unchanged, project-specific policy
- `ai-review` job on `self-hosted` runner:
  - `actions/checkout@v4`
  - `uses: WillIsback/ai-devops-toolkit/code-review@main` with `with:` block passing `vars` and `secrets`

The `runs-on: self-hosted` stays in the consumer workflow (it is infrastructure policy, not tool logic). The guardrail logic stays too.

---

## Versioning strategy

- Initial release: `@main` (acceptable while toolkit is single-consumer)
- When stable: tag `v1`, consumers can pin to `@v1`
- Breaking changes bump to `@v2`

---

## What is NOT in scope

- No other actions (doc-update, lint, etc.) in this iteration — YAGNI
- No changes to `reviewer.py` logic
- No GitHub org-level variable setup (already handled: `VLLM_BASE_URL` exists as repo/org var)

---

## Files changed

| File | Action |
|---|---|
| `~/ai-devops-toolkit/code-review/action.yml` | Create |
| `~/ai-devops-toolkit/code-review/reviewer.py` | Create (copy from NewsFoundry) |
| `~/ai-devops-toolkit/README.md` | Create |
| `NewsFoundry/scripts/ai_code_reviewer.py` | Delete (moved to toolkit) |
| `NewsFoundry/.github/workflows/ai-code-review.yml` | Simplify |
