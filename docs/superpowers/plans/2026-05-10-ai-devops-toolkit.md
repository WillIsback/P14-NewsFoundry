# ai-devops-toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the AI code review script from NewsFoundry into a standalone GitHub Composite Action at `/home/will/work/ai-devops-toolkit/`, then update NewsFoundry's workflow to consume it.

**Architecture:** A new git repository hosts `code-review/action.yml` (Composite Action) and `code-review/reviewer.py` (the Python script moved verbatim from NewsFoundry). NewsFoundry's workflow delegates entirely to `uses: WillIsback/ai-devops-toolkit/code-review@main`, keeping only project-specific policy (runner, guardrails).

**Tech Stack:** GitHub Actions Composite Actions, Python 3, openai/httpx/requests, gh CLI

---

## File Map

| Path | Action | Responsibility |
|---|---|---|
| `/home/will/work/ai-devops-toolkit/` | Create (git init) | New centralized repo root |
| `/home/will/work/ai-devops-toolkit/.gitignore` | Create | Ignore Python artifacts |
| `/home/will/work/ai-devops-toolkit/code-review/action.yml` | Create | Composite Action definition — inputs, steps |
| `/home/will/work/ai-devops-toolkit/code-review/reviewer.py` | Create (move) | AI review logic — unchanged from NewsFoundry |
| `/home/will/work/ai-devops-toolkit/code-review/tests/test_reviewer.py` | Create | Unit tests for pure functions |
| `/home/will/work/ai-devops-toolkit/README.md` | Create | Usage documentation |
| `NewsFoundry/scripts/ai_code_reviewer.py` | Delete | Moved to toolkit |
| `NewsFoundry/.github/workflows/ai-code-review.yml` | Modify | Simplify to single `uses:` call |

---

## Task 1: Initialize the toolkit repository

**Files:**
- Create: `/home/will/work/ai-devops-toolkit/.gitignore`

- [ ] **Step 1: Create directory and init git**

```bash
cd /home/will/work
mkdir ai-devops-toolkit
cd ai-devops-toolkit
git init
git checkout -b main
```

Expected: `Initialized empty Git repository in /home/will/work/ai-devops-toolkit/.git/`

- [ ] **Step 2: Create .gitignore**

Create `/home/will/work/ai-devops-toolkit/.gitignore`:

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.env
dist/
```

- [ ] **Step 3: Commit**

```bash
cd /home/will/work/ai-devops-toolkit
git add .gitignore
git commit -m "chore: initialize ai-devops-toolkit repository"
```

---

## Task 2: Write tests for reviewer.py pure functions

**Files:**
- Create: `/home/will/work/ai-devops-toolkit/code-review/tests/__init__.py`
- Create: `/home/will/work/ai-devops-toolkit/code-review/tests/test_reviewer.py`

The two pure functions in `reviewer.py` are `build_vllm_models_url` and `split_diff_into_chunks`. Tests must be written before the files exist (TDD).

- [ ] **Step 1: Create test directory**

```bash
mkdir -p /home/will/work/ai-devops-toolkit/code-review/tests
touch /home/will/work/ai-devops-toolkit/code-review/tests/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `/home/will/work/ai-devops-toolkit/code-review/tests/test_reviewer.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reviewer import build_vllm_models_url, split_diff_into_chunks


class TestBuildVllmModelsUrl:
    def test_base_url_with_v1_suffix(self):
        url = build_vllm_models_url("http://192.168.1.87:30000/v1")
        assert url == "http://192.168.1.87:30000/v1/models"

    def test_base_url_without_v1_suffix(self):
        url = build_vllm_models_url("http://192.168.1.87:30000")
        assert url == "http://192.168.1.87:30000/v1/models"

    def test_base_url_with_trailing_slash(self):
        url = build_vllm_models_url("http://192.168.1.87:30000/v1/")
        assert url == "http://192.168.1.87:30000/v1/models"


class TestSplitDiffIntoChunks:
    def test_small_diff_returns_single_chunk(self):
        diff = "line one\nline two\nline three"
        chunks = split_diff_into_chunks(diff, max_tokens=1000)
        assert len(chunks) == 1
        assert chunks[0] == diff

    def test_large_diff_splits_into_multiple_chunks(self):
        # Each word counts as 1 token; 300 words per line × 10 lines = 3000 tokens
        line = " ".join(["word"] * 300)
        diff = "\n".join([line] * 10)
        chunks = split_diff_into_chunks(diff, max_tokens=500)
        assert len(chunks) > 1

    def test_empty_diff_returns_single_empty_chunk(self):
        chunks = split_diff_into_chunks("")
        assert len(chunks) == 1
        assert chunks[0] == ""
```

- [ ] **Step 3: Run tests — expect ImportError (reviewer.py does not exist yet)**

```bash
cd /home/will/work/ai-devops-toolkit
pip install pytest --quiet
python -m pytest code-review/tests/test_reviewer.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'reviewer'` — confirms tests are wired but source is missing.

- [ ] **Step 4: Commit tests**

```bash
cd /home/will/work/ai-devops-toolkit
git add code-review/tests/
git commit -m "test: add unit tests for reviewer pure functions"
```

---

## Task 3: Move reviewer.py into the toolkit

**Files:**
- Create: `/home/will/work/ai-devops-toolkit/code-review/reviewer.py` (copy from NewsFoundry)
- Delete: `/home/will/formation_OC/P14/NewsFoundry/scripts/ai_code_reviewer.py`

- [ ] **Step 1: Copy the script**

```bash
cp /home/will/formation_OC/P14/NewsFoundry/scripts/ai_code_reviewer.py \
   /home/will/work/ai-devops-toolkit/code-review/reviewer.py
```

- [ ] **Step 2: Run tests — expect all PASS**

```bash
cd /home/will/work/ai-devops-toolkit
pip install openai httpx requests --quiet
python -m pytest code-review/tests/test_reviewer.py -v
```

Expected output:
```
PASSED code-review/tests/test_reviewer.py::TestBuildVllmModelsUrl::test_base_url_with_v1_suffix
PASSED code-review/tests/test_reviewer.py::TestBuildVllmModelsUrl::test_base_url_without_v1_suffix
PASSED code-review/tests/test_reviewer.py::TestBuildVllmModelsUrl::test_base_url_with_trailing_slash
PASSED code-review/tests/test_reviewer.py::TestSplitDiffIntoChunks::test_small_diff_returns_single_chunk
PASSED code-review/tests/test_reviewer.py::TestSplitDiffIntoChunks::test_large_diff_splits_into_multiple_chunks
PASSED code-review/tests/test_reviewer.py::TestSplitDiffIntoChunks::test_empty_diff_returns_single_empty_chunk
6 passed
```

- [ ] **Step 3: Delete the original from NewsFoundry**

```bash
rm /home/will/formation_OC/P14/NewsFoundry/scripts/ai_code_reviewer.py
```

- [ ] **Step 4: Commit toolkit addition**

```bash
cd /home/will/work/ai-devops-toolkit
git add code-review/reviewer.py
git commit -m "feat: add reviewer.py — moved from NewsFoundry/scripts"
```

- [ ] **Step 5: Commit deletion in NewsFoundry**

```bash
cd /home/will/formation_OC/P14/NewsFoundry
git add scripts/ai_code_reviewer.py
git commit -m "refactor: remove reviewer script — moved to WillIsback/ai-devops-toolkit"
```

---

## Task 4: Create the Composite Action (action.yml)

**Files:**
- Create: `/home/will/work/ai-devops-toolkit/code-review/action.yml`

- [ ] **Step 1: Write action.yml**

Create `/home/will/work/ai-devops-toolkit/code-review/action.yml`:

```yaml
name: AI Code Review
description: >
  Review a GitHub Pull Request using a self-hosted vLLM instance.
  Posts a structured Markdown comment directly on the PR.

inputs:
  vllm-url:
    description: 'Base URL of the vLLM server (e.g. http://192.168.1.87:30000/v1)'
    required: true
  github-token:
    description: 'GitHub token for fetching PR diff and posting the review comment'
    required: true
  vllm-model:
    description: 'Override model ID. Auto-detected from /v1/models if empty.'
    required: false
    default: ''
  vllm-timeout:
    description: 'Total request timeout in seconds'
    required: false
    default: '120'
  vllm-retries:
    description: 'Number of retries on LLM request failure'
    required: false
    default: '2'

runs:
  using: composite
  steps:
    - name: Install Python dependencies
      shell: bash
      run: pip install openai httpx requests --quiet

    - name: Validate required inputs
      shell: bash
      run: |
        if [ -z "${{ inputs.vllm-url }}" ]; then
          echo "::error::Input 'vllm-url' is required but was not provided."
          exit 1
        fi

    - name: Run AI Code Review
      shell: bash
      env:
        GITHUB_TOKEN: ${{ inputs.github-token }}
        VLLM_BASE_URL: ${{ inputs.vllm-url }}
        VLLM_MODEL: ${{ inputs.vllm-model }}
        VLLM_TIMEOUT: ${{ inputs.vllm-timeout }}
        VLLM_RETRIES: ${{ inputs.vllm-retries }}
        GITHUB_REPOSITORY: ${{ github.repository }}
        PULL_REQUEST_NUMBER: ${{ github.event.pull_request.number }}
      run: python3 ${{ github.action_path }}/reviewer.py
```

- [ ] **Step 2: Commit**

```bash
cd /home/will/work/ai-devops-toolkit
git add code-review/action.yml
git commit -m "feat: add composite action definition for code-review"
```

---

## Task 5: Write README

**Files:**
- Create: `/home/will/work/ai-devops-toolkit/README.md`

- [ ] **Step 1: Write README.md**

Create `/home/will/work/ai-devops-toolkit/README.md`:

```markdown
# ai-devops-toolkit

Centralized GitHub Composite Actions for WillIsback projects.

---

## Actions

### `code-review`

Reviews a Pull Request diff using a self-hosted [vLLM](https://github.com/vllm-project/vllm) instance and posts a structured Markdown comment on the PR.

#### Usage

```yaml
- name: Checkout code
  uses: actions/checkout@v4
  with:
    fetch-depth: 0

- name: AI Code Review
  uses: WillIsback/ai-devops-toolkit/code-review@main
  with:
    vllm-url: ${{ vars.VLLM_BASE_URL }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

#### Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `vllm-url` | yes | — | Base URL of the vLLM server |
| `github-token` | yes | — | GitHub token (use `secrets.GITHUB_TOKEN`) |
| `vllm-model` | no | `""` | Override model ID (auto-detected if empty) |
| `vllm-timeout` | no | `120` | Total request timeout (seconds) |
| `vllm-retries` | no | `2` | Retries on LLM request failure |

#### Prerequisites

- A self-hosted GitHub Actions runner with network access to your vLLM instance
- Repository/organization variable `VLLM_BASE_URL` set to your vLLM endpoint

#### Model detection

The action auto-detects the loaded model by querying `/v1/models`. Set `vllm-model` only to override.
```

- [ ] **Step 2: Commit**

```bash
cd /home/will/work/ai-devops-toolkit
git add README.md
git commit -m "docs: add README with code-review action usage"
```

---

## Task 6: Simplify NewsFoundry's workflow

**Files:**
- Modify: `/home/will/formation_OC/P14/NewsFoundry/.github/workflows/ai-code-review.yml`

- [ ] **Step 1: Replace the workflow content**

Overwrite `/home/will/formation_OC/P14/NewsFoundry/.github/workflows/ai-code-review.yml` with:

```yaml
name: AI Code Review on PR

on:
  pull_request:
    types: [opened, synchronize, reopened, labeled]
    paths:
      - "backend/**"
      - "frontend/**"
      - ".github/workflows/**"

permissions:
  pull-requests: write
  contents: read

jobs:
  ai-review-skipped:
    name: AI Review Guardrails
    runs-on: ubuntu-latest
    if: >-
      ${{
        !contains(fromJson('["OWNER","MEMBER","COLLABORATOR"]'), github.event.pull_request.author_association)
        && !contains(github.event.pull_request.labels.*.name, 'safe-to-test')
      }}
    steps:
      - name: Explain why AI review is skipped
        run: |
          echo "AI review skipped by policy."
          echo "Allowed automatically for internal contributors (OWNER/MEMBER/COLLABORATOR)."
          echo "For external PRs/forks, a maintainer must add the 'safe-to-test' label to run manually."

  ai-review:
    name: AI Code Review
    runs-on: self-hosted
    timeout-minutes: 10
    if: >-
      ${{
        contains(fromJson('["OWNER","MEMBER","COLLABORATOR"]'), github.event.pull_request.author_association)
        || contains(github.event.pull_request.labels.*.name, 'safe-to-test')
      }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: AI Code Review
        uses: WillIsback/ai-devops-toolkit/code-review@main
        with:
          vllm-url: ${{ vars.VLLM_BASE_URL }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          vllm-model: ${{ vars.VLLM_MODEL || '' }}
          vllm-timeout: ${{ vars.VLLM_TIMEOUT || '120' }}
          vllm-retries: ${{ vars.VLLM_RETRIES || '2' }}
```

- [ ] **Step 2: Commit in NewsFoundry**

```bash
cd /home/will/formation_OC/P14/NewsFoundry
git add .github/workflows/ai-code-review.yml
git commit -m "refactor: delegate AI review to WillIsback/ai-devops-toolkit composite action"
```

---

## Task 7: Final verification

- [ ] **Step 1: Verify toolkit structure**

```bash
find /home/will/work/ai-devops-toolkit -type f | sort
```

Expected:
```
/home/will/work/ai-devops-toolkit/.gitignore
/home/will/work/ai-devops-toolkit/README.md
/home/will/work/ai-devops-toolkit/code-review/action.yml
/home/will/work/ai-devops-toolkit/code-review/reviewer.py
/home/will/work/ai-devops-toolkit/code-review/tests/__init__.py
/home/will/work/ai-devops-toolkit/code-review/tests/test_reviewer.py
```

- [ ] **Step 2: Run full test suite**

```bash
cd /home/will/work/ai-devops-toolkit
python -m pytest code-review/tests/ -v
```

Expected: `6 passed`

- [ ] **Step 3: Verify NewsFoundry script is gone**

```bash
ls /home/will/formation_OC/P14/NewsFoundry/scripts/
```

Expected: empty directory or no `ai_code_reviewer.py`

- [ ] **Step 4: Verify NewsFoundry workflow references the toolkit**

```bash
grep "ai-devops-toolkit" /home/will/formation_OC/P14/NewsFoundry/.github/workflows/ai-code-review.yml
```

Expected: `uses: WillIsback/ai-devops-toolkit/code-review@main`

- [ ] **Step 5: Validate YAML is well-formed**

```bash
python3 -c "
import yaml
for f in [
    '/home/will/work/ai-devops-toolkit/code-review/action.yml',
    '/home/will/formation_OC/P14/NewsFoundry/.github/workflows/ai-code-review.yml',
]:
    yaml.safe_load(open(f))
    print(f'OK: {f}')
"
```

Expected:
```
OK: /home/will/work/ai-devops-toolkit/code-review/action.yml
OK: /home/will/formation_OC/P14/NewsFoundry/.github/workflows/ai-code-review.yml
```

- [ ] **Step 6: Show git log for both repos**

```bash
echo "=== ai-devops-toolkit ===" && git -C /home/will/work/ai-devops-toolkit log --oneline
echo "=== NewsFoundry ===" && git -C /home/will/formation_OC/P14/NewsFoundry log --oneline -5
```
