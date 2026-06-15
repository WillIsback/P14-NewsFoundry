# Release Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un workflow GitHub Actions qui, après chaque merge réussi sur `main`, bumpe la version dans `backend/pyproject.toml` et `frontend/package.json`, crée une GitHub Release avec notes auto-générées, et publie l'image Docker du backend sur `ghcr.io`.

**Architecture:** Un seul fichier `.github/workflows/release.yml` contenant deux jobs séquentiels : `bump-and-release` (lecture version → calcul → mise à jour fichiers → commit/push → tag → Release) et `docker-publish` (checkout au tag → build → push ghcr.io). Le workflow se déclenche via `workflow_run` sur `Backend Tests` avec une condition de succès explicite et un groupe de concurrence pour éviter les race conditions.

**Tech Stack:** GitHub Actions, `python3` (natif dans les runners Ubuntu) pour la manipulation TOML, `jq` (natif dans les runners Ubuntu) pour JSON, `docker/build-push-action`, `docker/login-action`, `docker/setup-buildx-action`, `actions/github-script` pour la création de Release via l'API.

---

## Structure des fichiers

| Action | Chemin |
|--------|--------|
| Créer | `.github/workflows/release.yml` |

Aucun autre fichier à modifier. La logique de version bump est intégralement dans le workflow YAML.

---

### Task 1 : Créer l'issue GitHub et la branche de travail

**Files:**
- Aucun fichier à modifier dans cette tâche

- [ ] **Step 1 : Créer l'issue GitHub**

```bash
gh issue create \
  --title "feat: pipeline de release automatisé (bump version + image Docker)" \
  --body "## Objectif

Ajouter un workflow CI/CD \`.github/workflows/release.yml\` qui, après chaque merge réussi sur \`main\` (validé par Backend Tests) :

1. Bumpe la version dans \`backend/pyproject.toml\` et \`frontend/package.json\`
   - Logique : minor++ jusqu'à minor=40, puis major++/minor=0
2. Commite et pousse le bump directement sur \`main\`
3. Crée un tag \`vX.Y.0\` et une GitHub Release avec notes auto-générées
4. Build et publie l'image Docker sur \`ghcr.io/<owner>/newsfoundry-backend\` avec les tags \`vX.Y.0\` et \`latest\`

## Spec

Voir \`docs/specs/2026-06-15-release-pipeline-design.md\`" \
  --label "enhancement"
```

Relever le numéro d'issue affiché (ex: `#121`). Il sera utilisé dans le nom de la branche.

- [ ] **Step 2 : Créer et se placer sur la branche de travail**

```bash
# Remplacer 121 par le vrai numéro d'issue
git checkout -b feat/121-release-pipeline
```

- [ ] **Step 3 : Vérifier qu'on est sur la bonne branche**

```bash
git branch --show-current
```

Expected output: `feat/121-release-pipeline`

---

### Task 2 : Créer le workflow `.github/workflows/release.yml`

**Files:**
- Créer : `.github/workflows/release.yml`

- [ ] **Step 1 : Créer le fichier workflow**

Créer `.github/workflows/release.yml` avec le contenu suivant :

```yaml
name: Release

# Déclenché uniquement quand "Backend Tests" se termine sur la branche main.
# types: [completed] couvre succès ET échec — la condition `if` du job filtre
# explicitement sur conclusion == 'success'.
on:
  workflow_run:
    workflows: ["Backend Tests"]
    types: [completed]
    branches: [main]

# Un seul pipeline à la fois. cancel-in-progress: false met en file d'attente
# plutôt qu'annuler une release déjà en cours.
concurrency:
  group: release-pipeline
  cancel-in-progress: false

permissions:
  contents: write  # push vers main + création tag + release
  packages: write  # push vers ghcr.io

jobs:
  # ── Job 1 : bump version + GitHub Release ──────────────────────────────────
  bump-and-release:
    name: Bump version & create GitHub Release
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    outputs:
      new_version: ${{ steps.bump.outputs.new_version }}

    steps:
      - name: Checkout main
        uses: actions/checkout@v4
        with:
          ref: main
          fetch-depth: 0  # Historique complet requis pour generate_release_notes

      - name: Configure Git identity
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Compute new version
        id: bump
        run: |
          # Lecture robuste via Python — insensible aux variations d'espacement TOML
          CURRENT=$(python3 -c "
          import re, sys
          content = open('backend/pyproject.toml').read()
          m = re.search(r'^version\s*=\s*\"([^\"]+)\"', content, re.MULTILINE)
          print(m.group(1) if m else sys.exit(1))
          ")

          MAJOR=$(echo "$CURRENT" | cut -d. -f1)
          MINOR=$(echo "$CURRENT" | cut -d. -f2)

          # Logique custom : minor++ jusqu'à minor=40, puis major++/minor reset
          if [ "$MINOR" -ge 40 ]; then
            NEW_VERSION="$((MAJOR + 1)).0.0"
          else
            NEW_VERSION="${MAJOR}.$((MINOR + 1)).0"
          fi

          echo "Version bump : $CURRENT → $NEW_VERSION"

          # Exposition aux étapes suivantes via GITHUB_ENV et GITHUB_OUTPUT
          echo "NEW_VERSION=${NEW_VERSION}" >> "$GITHUB_ENV"
          echo "new_version=v${NEW_VERSION}" >> "$GITHUB_OUTPUT"

      - name: Update backend/pyproject.toml
        run: |
          python3 -c "
          import re, os
          path = 'backend/pyproject.toml'
          content = open(path).read()
          new_ver = os.environ['NEW_VERSION']
          content = re.sub(
              r'^(version\s*=\s*)\"[^\"]+\"',
              lambda m: m.group(1) + '\"' + new_ver + '\"',
              content,
              flags=re.MULTILINE
          )
          open(path, 'w').write(content)
          "

      - name: Update frontend/package.json
        run: |
          jq --arg v "$NEW_VERSION" '.version = $v' frontend/package.json > tmp.json \
            && mv tmp.json frontend/package.json

      - name: Commit & push version bump
        # Note : les commits via GITHUB_TOKEN ne déclenchent pas d'autres
        # workflows — pas de boucle infinie possible ici.
        run: |
          git add backend/pyproject.toml frontend/package.json
          git commit -m "chore: bump version to v${NEW_VERSION}"
          git push origin main

      - name: Create and push tag
        run: |
          git tag "v${NEW_VERSION}"
          git push origin "v${NEW_VERSION}"

      - name: Create GitHub Release
        uses: actions/github-script@v7
        env:
          TAG_NAME: ${{ steps.bump.outputs.new_version }}
        with:
          script: |
            await github.rest.repos.createRelease({
              owner: context.repo.owner,
              repo: context.repo.repo,
              tag_name: process.env.TAG_NAME,
              name: `Release ${process.env.TAG_NAME}`,
              generate_release_notes: true,
            });

  # ── Job 2 : build + push image Docker ──────────────────────────────────────
  docker-publish:
    name: Build & push Docker image
    needs: bump-and-release
    runs-on: ubuntu-latest

    steps:
      - name: Checkout at release tag
        uses: actions/checkout@v4
        with:
          ref: ${{ needs.bump-and-release.outputs.new_version }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: ./backend
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/newsfoundry-backend:${{ needs.bump-and-release.outputs.new_version }}
            ghcr.io/${{ github.repository_owner }}/newsfoundry-backend:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

### Task 3 : Valider la syntaxe YAML avant de pousser

**Files:**
- Lire : `.github/workflows/release.yml`

- [ ] **Step 1 : Installer yamllint**

```bash
pip install yamllint --quiet
```

- [ ] **Step 2 : Valider la syntaxe YAML**

```bash
yamllint -d "{extends: default, rules: {line-length: {max: 120}}}" \
  .github/workflows/release.yml
```

Expected output: aucune erreur. En cas d'erreur, corriger le fichier avant de continuer.

- [ ] **Step 3 : Vérifier la structure du fichier avec python**

```bash
python3 -c "
import yaml, sys
with open('.github/workflows/release.yml') as f:
    doc = yaml.safe_load(f)
jobs = doc.get('jobs', {})
assert 'bump-and-release' in jobs, 'job bump-and-release manquant'
assert 'docker-publish' in jobs, 'job docker-publish manquant'
assert doc['jobs']['docker-publish']['needs'] == 'bump-and-release', 'dépendance manquante'
outputs = doc['jobs']['bump-and-release'].get('outputs', {})
assert 'new_version' in outputs, 'output new_version manquant'
print('✅ Structure du workflow valide')
"
```

Expected output: `✅ Structure du workflow valide`

- [ ] **Step 4 : Commiter**

```bash
git add .github/workflows/release.yml
git commit -m "feat: ajoute le workflow de release automatisé (bump + Docker)"
```

---

### Task 4 : Créer la PR et merger

**Files:**
- Aucun nouveau fichier

- [ ] **Step 1 : Pousser la branche**

```bash
git push -u origin feat/121-release-pipeline
```

- [ ] **Step 2 : Créer la PR**

```bash
# Remplacer 121 par le vrai numéro d'issue
gh pr create \
  --title "feat(#121): pipeline de release automatisé (bump version + image Docker)" \
  --body "$(cat <<'EOF'
## Résumé

Ajoute `.github/workflows/release.yml` qui, après chaque `Backend Tests` réussi sur `main` :

- Calcule la nouvelle version (minor++ jusqu'à 40, puis major++)
- Met à jour `backend/pyproject.toml` et `frontend/package.json`
- Commite et pousse le bump directement sur `main` via `GITHUB_TOKEN`
- Crée un tag `vX.Y.0` et une GitHub Release avec notes auto-générées
- Build et pousse l'image Docker sur `ghcr.io/<owner>/newsfoundry-backend` (`vX.Y.0` + `latest`)

## Décisions de design notables

- `concurrency: group: release-pipeline` → pas de race condition si deux PR sont mergées rapidement
- Commit via `GITHUB_TOKEN` → ne re-déclenche pas `Backend Tests` (pas de boucle infinie)
- Python natif pour le parsing TOML → robuste aux variations de format

Closes #121
EOF
)"
```

- [ ] **Step 3 : Vérifier que le check `PR Issue Validation` passe**

```bash
gh pr checks
```

Expected : le check `Validate PR Links Issue` doit être vert (la PR contient `Closes #121`).

- [ ] **Step 4 : Merger la PR**

```bash
gh pr merge --squash --delete-branch
```

---

### Task 5 : Vérification post-merge

**Files:**
- Lire : `.github/workflows/release.yml` (en cas de debug)

- [ ] **Step 1 : Surveiller le déclenchement du workflow**

Après le merge, attendre que `Backend Tests` se termine sur `main`, puis :

```bash
gh run list --workflow=release.yml --limit=5
```

Expected : un run apparaît avec le statut `in_progress` ou `success`.

- [ ] **Step 2 : Vérifier les logs du job bump-and-release**

```bash
# Récupérer l'ID du run le plus récent
RUN_ID=$(gh run list --workflow=release.yml --limit=1 --json databaseId -q '.[0].databaseId')
gh run view "$RUN_ID" --log
```

Vérifier dans les logs :
- La ligne `Version bump : 0.1.0 → 0.2.0`
- Le commit poussé sur main
- Le tag `v0.2.0` créé

- [ ] **Step 3 : Vérifier la GitHub Release créée**

```bash
gh release list --limit=3
```

Expected : une release `v0.2.0` (ou la version suivante) apparaît avec `generate_release_notes`.

- [ ] **Step 4 : Vérifier l'image Docker sur ghcr.io**

```bash
gh api /user/packages/container/newsfoundry-backend/versions --jq '.[0:3] | .[].metadata.container.tags'
```

Expected : les tags `v0.2.0` et `latest` sont présents.

- [ ] **Step 5 : Vérifier la mise à jour des fichiers de version**

```bash
git pull origin main
grep '^version' backend/pyproject.toml
python3 -c "import json; print(json.load(open('frontend/package.json'))['version'])"
```

Expected : les deux fichiers affichent la nouvelle version (ex: `0.2.0`).

---

## Checklist de protection de `main`

Si le job `Commit & push version bump` échoue avec `refusing to allow a GitHub App to create or update workflow file`, vérifier dans **Settings → Branches → Branch protection rules → main** :

- [ ] Autoriser `github-actions[bot]` à bypass les règles de protection (option "Allow specified actors to bypass required pull requests")

Si le push échoue avec `403 Permission denied`, vérifier dans **Settings → Actions → General → Workflow permissions** :

- [ ] "Read and write permissions" est activé
