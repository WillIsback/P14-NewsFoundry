# Validate ai-devops-toolkit v0.0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create branch `feat/validate-ai-toolkit` in NewsFoundry, pin code-review to `@v0.0.2`, test docgen via 3 invocation methods on a real file, then open a PR that triggers the code-review action as live end-to-end validation.

**Architecture:** Single NewsFoundry branch. code-review validated by the PR trigger. docgen validated locally with 3 successive runs on `frontend/src/lib/auth-helpers.ts` (no JSDoc): direct binary, `uv run`, `pnpm exec`. The toolkit package.json gains a `bin` field to support `pnpm exec docgen` from consumer projects.

**Tech Stack:** Rust (docgen binary), GitHub Actions Composite Action (code-review), git2 (branch workflow), pnpm, uv/maturin.

---

## Files

| File | Action |
|---|---|
| `NewsFoundry/.github/workflows/ai-code-review.yml` | Modify — pin `@v0.0.2` |
| `NewsFoundry/frontend/src/lib/auth-helpers.ts` | Modified by docgen (JSDoc added) |
| `ai-devops-toolkit/package.json` | Modify — add `"bin"` field |

---

## Task 1: Create branch `feat/validate-ai-toolkit`

**Files:**
- Repo: `/home/will/formation_OC/P14/NewsFoundry`

- [ ] **Step 1: Create and switch to branch**

```bash
cd ~/formation_OC/P14/NewsFoundry
git checkout -b feat/validate-ai-toolkit
```

Expected output: `Switched to a new branch 'feat/validate-ai-toolkit'`

- [ ] **Step 2: Verify clean working tree**

```bash
git status
```

Expected: `nothing to commit, working tree clean`

---

## Task 2: Pin code-review action to `@v0.0.2`

**Files:**
- Modify: `.github/workflows/ai-code-review.yml:47`

- [ ] **Step 1: Update the `uses:` line**

In `.github/workflows/ai-code-review.yml`, change:

```yaml
        uses: WillIsback/ai-devops-toolkit/code-review@main
```

to:

```yaml
        uses: WillIsback/ai-devops-toolkit/code-review@v0.0.2
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ai-code-review.yml
git commit -m "ci: pin code-review action to v0.0.2"
```

---

## Task 3: Download `bin/docgen` via pnpm postinstall

**Files:**
- Repo: `/home/will/work/ai-devops-toolkit`

- [ ] **Step 1: Run pnpm install in toolkit**

```bash
cd ~/work/ai-devops-toolkit
pnpm install
```

Expected output includes: `[docgen] Binary installed to .../bin/docgen`

- [ ] **Step 2: Verify binary is present and executable**

```bash
ls -lh ~/work/ai-devops-toolkit/bin/docgen
~/work/ai-devops-toolkit/bin/docgen --help
```

Expected: binary listed, help output printed with `Generate docstrings using a local vLLM instance.`

---

## Task 4: Test Method 1 — direct binary

**Files:**
- Target: `frontend/src/lib/auth-helpers.ts` (2 functions, no JSDoc)
- CWD must be the NewsFoundry git root

- [ ] **Step 1: Confirm target file has no JSDoc**

```bash
cd ~/formation_OC/P14/NewsFoundry
grep -c '/\*\*' frontend/src/lib/auth-helpers.ts
```

Expected: `0`

- [ ] **Step 2: Run docgen via direct binary**

```bash
~/work/ai-devops-toolkit/bin/docgen frontend/src/lib/auth-helpers.ts
```

Expected output:
```
Auto-detected model: <model-name>
Processing 1 file(s) in batches of 4...
Applying changes via git branch...
Done. Docstrings applied.
```

- [ ] **Step 3: Verify docstrings were added and committed**

```bash
git log --oneline -3
grep '/\*\*' frontend/src/lib/auth-helpers.ts
```

Expected: two merge commits in log (docgen branch + merge commit), JSDoc blocks present in file.

---

## Task 5: Test Method 2 — `uv run docgen`

**Files:**
- Target: `frontend/src/lib/auth-helpers.ts` (already has JSDoc — use `--force`)
- CWD: NewsFoundry git root

- [ ] **Step 1: Confirm venv binary exists**

```bash
ls ~/work/ai-devops-toolkit/.venv/bin/docgen
```

Expected: path printed, no error.

- [ ] **Step 2: Run docgen via uv**

```bash
cd ~/formation_OC/P14/NewsFoundry
uv run --project ~/work/ai-devops-toolkit docgen frontend/src/lib/auth-helpers.ts --force
```

Expected output identical to Task 4 Step 2.

- [ ] **Step 3: Verify new merge commits in log**

```bash
git log --oneline -5
```

Expected: 2 new commits (docgen branch + merge) on top of Task 4's commits.

---

## Task 6: Add `bin` field to toolkit package.json

This enables `pnpm exec docgen` from any project that installs the toolkit as a dependency.

**Files:**
- Modify: `/home/will/work/ai-devops-toolkit/package.json`

- [ ] **Step 1: Add `bin` field**

Edit `~/work/ai-devops-toolkit/package.json` to:

```json
{
  "name": "ai-devops-toolkit",
  "bin": {
    "docgen": "./bin/docgen"
  },
  "scripts": {
    "docgen": "./bin/docgen",
    "postinstall": "node scripts/npm-postinstall.js"
  }
}
```

- [ ] **Step 2: Commit in toolkit repo**

```bash
cd ~/work/ai-devops-toolkit
git add package.json
git commit -m "feat(pkg): expose docgen as a bin entry for pnpm exec"
```

- [ ] **Step 3: Push to toolkit main**

```bash
git push origin main
```

---

## Task 7: Test Method 3 — `pnpm exec docgen` from NewsFoundry

**Files:**
- Target: `frontend/src/lib/auth-helpers.ts` (use `--force`)
- CWD: NewsFoundry git root

- [ ] **Step 1: Install toolkit as dev dependency in NewsFoundry frontend**

```bash
cd ~/formation_OC/P14/NewsFoundry/frontend
pnpm add -D ~/work/ai-devops-toolkit
```

Expected: postinstall runs, `[docgen] Binary installed to node_modules/ai-devops-toolkit/bin/docgen`, symlink created at `node_modules/.bin/docgen`.

- [ ] **Step 2: Verify bin is linked**

```bash
ls -la node_modules/.bin/docgen
```

Expected: symlink pointing to `../ai-devops-toolkit/bin/docgen`

- [ ] **Step 3: Run docgen via pnpm exec from NewsFoundry root**

```bash
cd ~/formation_OC/P14/NewsFoundry
pnpm --dir frontend exec docgen frontend/src/lib/auth-helpers.ts --force
```

Expected output identical to Task 4 Step 2.

- [ ] **Step 4: Verify new commits**

```bash
git log --oneline -7
```

Expected: 2 more commits (docgen branch + merge).

- [ ] **Step 5: Commit frontend package changes**

```bash
cd ~/formation_OC/P14/NewsFoundry
git add frontend/package.json frontend/pnpm-lock.yaml
git commit -m "feat(frontend): add ai-devops-toolkit as dev dep for pnpm exec docgen"
```

---

## Task 8: Create Pull Request

- [ ] **Step 1: Push branch**

```bash
cd ~/formation_OC/P14/NewsFoundry
git push -u origin feat/validate-ai-toolkit
```

- [ ] **Step 2: Create PR**

```bash
gh pr create \
  --title "feat: validate ai-devops-toolkit v0.0.2 — code-review + docgen" \
  --body "$(cat <<'EOF'
## Summary

- Pins `code-review` action to `@v0.0.2` (Rust binary, stable release)
- Validates docgen via 3 invocation methods on `frontend/src/lib/auth-helpers.ts`
- Adds `ai-devops-toolkit` as a frontend dev dependency for `pnpm exec docgen`

## Docgen test results

| Method | Command | Result |
|---|---|---|
| Direct binary | `~/work/ai-devops-toolkit/bin/docgen <file>` | ✅ |
| uv run | `uv run --project ~/work/ai-devops-toolkit docgen <file>` | ✅ |
| pnpm exec | `pnpm --dir frontend exec docgen <file>` | ✅ |

## Validation

Opening this PR triggers `ai-code-review.yml` which downloads `code-review-cli-linux-amd64` from `v0.0.2` and posts a review comment — live end-to-end test for the Rust binary.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Confirm code-review action triggered**

```bash
gh pr checks
```

Expected: `AI Code Review` check running or completed with a comment posted on the PR.
