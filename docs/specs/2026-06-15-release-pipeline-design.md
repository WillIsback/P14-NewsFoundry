# Design : Pipeline de Release Automatisé

**Date :** 2026-06-15
**Statut :** Approuvé

---

## Objectif

Ajouter un workflow CI/CD qui, après chaque merge réussi sur `main` (validé par les tests backend), publie automatiquement une GitHub Release versionnée et l'image Docker du backend sur GitHub Container Registry (ghcr.io).

---

## Architecture

### Déclencheur

```yaml
on:
  workflow_run:
    workflows: ["Backend Tests"]
    types: [completed]
    branches: [main]
```

`types: [completed]` se déclenche quelle que soit la conclusion (succès, échec, annulation). La condition de succès est vérifiée explicitement au niveau du job :

```yaml
jobs:
  bump-and-release:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

### Concurrence

Pour éviter les race conditions si deux PR sont mergées rapidement :

```yaml
concurrency:
  group: release-pipeline
  cancel-in-progress: false  # file d'attente, ne pas annuler une release en cours
```

### Comportement du GITHUB_TOKEN sur les push

Les commits poussés par `GITHUB_TOKEN` ne déclenchent pas d'autres workflows GitHub Actions. C'est un comportement intentionnel ici : le commit `chore: bump version...` ne re-déclenche pas `Backend Tests`, ce qui empêche toute boucle infinie. Le commit de bump n'est pas testé par le CI — ce qui est acceptable pour un changement de métadonnées.

### Fichier

`.github/workflows/release.yml`

### Deux jobs séquentiels

```
[bump-and-release]
  1. Lire la version actuelle depuis backend/pyproject.toml
  2. Calculer la nouvelle version (logique custom)
  3. Mettre à jour backend/pyproject.toml + frontend/package.json
  4. Commit + push sur main ("chore: bump version to vX.Y.0")
  5. Créer le tag git vX.Y.0
  6. Créer la GitHub Release (auto-generated notes)
        ↓
[docker-publish]  (needs: bump-and-release)
  1. Checkout au tag vX.Y.0
  2. Authentification ghcr.io via GITHUB_TOKEN
  3. Build depuis backend/Dockerfile
  4. Push des deux tags (versionné + latest)
```

### Output inter-jobs

`bump-and-release` expose `new_version` (ex: `v1.2.0`) comme output GitHub Actions, consommé par `docker-publish` pour le tag de l'image.

---

## Logique de bump de version

### Règle

| Condition | Résultat |
|-----------|----------|
| `minor < 40` | `MAJOR.MINOR+1.0` |
| `minor >= 40` | `MAJOR+1.0.0` |

### Exemples

```
0.1.0  →  0.2.0
0.39.0 →  0.40.0
0.40.0 →  1.0.0
1.40.0 →  2.0.0
```

### Script de bump

Python est disponible nativement dans GitHub Actions et gère le TOML sans ambiguïté de format :

```bash
# Lecture de la version courante via Python (robuste aux variations de format TOML)
CURRENT=$(python3 -c "
import re, sys
content = open('backend/pyproject.toml').read()
m = re.search(r'^version\s*=\s*\"([^\"]+)\"', content, re.MULTILINE)
print(m.group(1) if m else sys.exit(1))
")

MAJOR=$(echo $CURRENT | cut -d. -f1)
MINOR=$(echo $CURRENT | cut -d. -f2)

if [ "$MINOR" -ge 40 ]; then
  NEW_VERSION="$((MAJOR + 1)).0.0"
else
  NEW_VERSION="${MAJOR}.$((MINOR + 1)).0"
fi
```

### Mise à jour des fichiers

**Source de vérité :** `backend/pyproject.toml` (lu en premier, version appliquée aux deux fichiers).

```bash
# backend/pyproject.toml — Python pour écriture TOML fiable
python3 -c "
import re
path = 'backend/pyproject.toml'
content = open(path).read()
content = re.sub(r'^(version\s*=\s*)\"[^\"]+\"', r'\1\"${NEW_VERSION}\"', content, flags=re.MULTILINE)
open(path, 'w').write(content)
"

# frontend/package.json — jq pour JSON valide
jq --arg v "$NEW_VERSION" '.version = $v' frontend/package.json > tmp.json \
  && mv tmp.json frontend/package.json
```

### Configuration de l'identité Git du bot

Requis avant tout commit automatisé :

```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
```

---

## Publication Docker

### Registry et tags

```
ghcr.io/willisback/newsfoundry-backend:vX.Y.0   ← tag versionné
ghcr.io/willisback/newsfoundry-backend:latest    ← alias courant
```

### Authentification

`GITHUB_TOKEN` natif — aucun secret externe requis.

### Optimisation du cache

Cache GitHub Actions (`type=gha`) pour éviter de rebuilder les layers inchangés (notamment le téléchargement du modèle ONNX fastembed).

```yaml
- uses: docker/build-push-action@v6
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

## Permissions requises

```yaml
permissions:
  contents: write   # push vers main + création tag + release
  packages: write   # push vers ghcr.io
```

## Point d'attention : protection de main

Si `main` a des règles de protection qui interdisent les push directs, il faudra autoriser le bot GitHub Actions (`github-actions[bot]`) à contourner cette règle dans **Settings → Branches → Branch protection rules**.

---

## GitHub Release

- **Type :** GitHub Release standard avec `generate_release_notes: true`
- **Tag :** `vX.Y.0`
- **Contenu :** Notes auto-générées depuis les PR mergées depuis la dernière release

---

## Workflow de mise en œuvre

Conformément au workflow du projet, cette fonctionnalité sera implémentée via :
1. Création d'une issue GitHub
2. Branche nommée `feat/<issue>-release-pipeline`
3. PR référençant l'issue (`Closes #<issue>`)
