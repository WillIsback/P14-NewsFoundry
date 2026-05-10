# NewsFoundry Backend

- Copier le fichier `.env.example` dans `.env`

- Ajuster les variables d'environnement selon le contexte:

```bash
APP_ENV=development
SEED_DEFAULT_USER=true
DEFAULT_USER_EMAIL=test@test.com
DEFAULT_USER_PASSWORD=test
```

En production, définis plutôt `APP_ENV=production` et mets `SEED_DEFAULT_USER=false`.

- Installer les dépendances:

```bash
uv sync
```

- Démarrer la base de données:

```bash
docker run \
  --name newsfoundry_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=newsfoundry \
  -p 5432:5432 \
  postgres:17
```

- Lancer le backend:

```bash
uv run --env-file .env src/main.py
```

## Pre-commit (backend seulement)

Le workflow `pre-commit` est configure a la racine du repo mais cible uniquement `backend/`:

- `ruff-format` pour formatter automatiquement
- `ruff --fix` pour lint + corrections automatiques
- `bandit` pour detecter des problemes de securite potentiels

Installation et execution:

```bash
uvx pre-commit install
uvx pre-commit run --all-files
```

---

## Admin Bootstrap (Production One-Shot)

Le bootstrap admin est un mécanisme **idempotent** pour créer un compte administrateur en production sans risque.

### Workflow

1. **Stockage des secrets** → Bitwarden vault
2. **Injection en env vars** → Railway injecte ADMIN_EMAIL et ADMIN_PASSWORD avant le deploy hook
3. **Exécution du bootstrap** → Deploy hook lance `uv run src/bootstrap.py`
4. **Vérification** → Script crée l'admin une fois, ignore les exécutions suivantes

### Setup Railway Deploy Hook

Dans le fichier `railway.toml` ou via Railway UI, ajouter:

```toml
[build]
builder = "nixpacks"
buildCommand = "uv sync"

[deploy]
startCommand = "uv run src/main.py"
releaseCommand = "uv run src/bootstrap.py"
```

Ou via Railway Dashboard:

- Service → Settings → Deploy → Release Command
- Entrer: `uv run src/bootstrap.py`

### Configuration des Secrets (Bitwarden → Railway)

1. Stocker dans Bitwarden:

   ```
   Username: admin@newsfoundry.com
   Password: <secure_password>
   ```

2. Ajouter dans Railway Variables d'env (via UI ou CLI):

   ```
   ADMIN_EMAIL=admin@newsfoundry.com
   ADMIN_PASSWORD=<secure_password>
   BOOTSTRAP_ENABLED=true
   ```

3. Railway les injecte automatiquement → Deploy hook les lit → Bootstrap crée l'admin

### Utilisation Locale (Dev/Test)

#### Via env vars

```bash
export ADMIN_EMAIL=admin@test.com
export ADMIN_PASSWORD=test123
uv run src/bootstrap.py
```

#### Via CLI args (plus pratique)

```bash
uv run src/bootstrap.py --email admin@test.com --password test123
```

#### Mode "dry run" (vérifier si admin existe)

```bash
uv run src/bootstrap.py --email noop@noop.com --password noop
# Output: ℹ Admin already exists (admin@test.com), skipping creation
```

### Comportement Idempotent

- **Première exécution** → Crée l'admin, exit 0 ✓
- **Deuxième exécution** → Admin existe, skip, exit 0 ✓
- **N-ième exécution** → Toujours skip, exit 0 ✓
- **Redéploiement Railway** → Deploy hook re-run, aucun risque ✓

### Dépannage

**Erreur: "ADMIN_EMAIL and ADMIN_PASSWORD must be provided"**

- Vérifier les secrets Railway sont bien injectés
- En local, utiliser `--email` et `--password` explicitement

**Erreur: "DATABASE_URL environment variable is not set"**

- En local: `export DATABASE_URL=postgresql://...`
- En Railway: vérifier que la DB est bien liée au service

**Le script crée plusieurs admins accidentellement**

- Impossible : table User.email est UNIQUE, et le bootstrap query sur role="admin"
- Il n'y aura jamais qu'un seul admin

### Futures Améliorations

- Endpoint de rotation de mot de passe admin (POST /admin/change-password)
- CLI Typer interactif pour multi-user bootstrap (dev seulement)
- Metrics: enregistrer chaque bootstrap attempt dans logs structurés
