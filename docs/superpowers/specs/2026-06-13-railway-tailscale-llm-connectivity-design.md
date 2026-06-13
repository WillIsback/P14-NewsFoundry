# Connectivité LLM en prod : Tailscale embarqué dans le conteneur backend

**Date :** 2026-06-13
**Statut :** Design validé
**Contexte issue :** suite de #70 (prod health & observability)

## Problème

Le backend Railway doit appeler un serveur vLLM auto-hébergé sur le GB10/DGX
Spark (`spark-787d-1`, IP tailnet `100.70.22.24:30000`), uniquement joignable
via le réseau Tailscale privé. Aujourd'hui :

- Le backend tape `http://100.70.22.24:30000/v1` **en direct**, sans accès au
  tailnet → timeout systématique. Le chat en prod est cassé.
- Le health endpoint `/api/v1/health` (ajouté en #70) le confirme :
  `overall=error`, `subsystems.llm = timeout after 10.0s`, `db=ok`.
- Un service tiers `railway-tailscale` (image jayhale, surcouche du
  `containerboot` officiel) était censé faire le pont mais **n'apparaît pas
  dans `tailscale status`** : il n'a jamais rejoint le tailnet. Il offre aussi
  peu de logs/contrôle (entrypoint qui pipe via `jq`).

L'infra maison est **privée par design** (LAN + Tailscale), sans domaine ni
ingress publique. Exposer vLLM publiquement (Traefik/Funnel) ajouterait une
surface d'attaque disproportionnée pour ce projet.

## Décision

Embarquer **Tailscale officiel directement dans le Dockerfile du backend**
(pas de service tiers). Le conteneur backend devient lui-même un node du
tailnet ; les appels LLM sont routés via un proxy local. vLLM reste 100% privé.

Décisions verrouillées avec l'utilisateur :

- **Auth key** : éphémère + reusable + taggée `tag:railway`. Pas de volume
  d'état (le node se ré-enregistre à chaque deploy, les nodes offline sont
  auto-nettoyés).
- **Conteneur** : reste **non-root** (`appuser` uid 1001). `tailscaled` en
  mode userspace ne requiert ni root ni `NET_ADMIN`.
- **Proxy scopé aux seuls appels LLM** : egress WorldNewsAPI/Sentry reste
  direct (Internet), pas via le tailnet.
- **Proxy HTTP sortant** de Tailscale (`--outbound-http-proxy-listen`), pas
  SOCKS5 → évite la dépendance `httpx[socks]` (la cible vLLM est en `http://`).

## Architecture

```
Conteneur backend (Railway, non-root appuser)
 ├─ tailscaled  (--tun=userspace-networking,
 │               --outbound-http-proxy-listen=localhost:1055)
 │     rejoint le tailnet via TS_AUTHKEY (éphémère, reusable, tag:railway)
 └─ uvicorn (app)
       ├─ client LLM (AsyncOpenAI) → httpx proxy=http://localhost:1055
       │      → tailnet → vLLM (100.70.22.24:30000 = spark-787d-1)
       └─ WorldNewsAPI / Sentry → Internet direct (pas de proxy)
```

`userspace-networking` ne crée pas d'interface kernel : seul le trafic envoyé
explicitement au proxy `:1055` passe par le tailnet, le reste sort normalement.

## Composants

### 1. Dockerfile + entrypoint

- Copier les binaires depuis l'image officielle, **version pinnée** (pas
  `stable`) :
  `COPY --from=tailscale/tailscale:vX.Y.Z /usr/local/bin/tailscaled /usr/local/bin/tailscale /usr/local/bin/`
- Créer `/app/.tailscale` (statedir + socket), `chown appuser`.
- Nouveau `docker-entrypoint.sh` (exécuté en `appuser`) :
  1. lance en arrière-plan
     `tailscaled --tun=userspace-networking --outbound-http-proxy-listen=localhost:1055 --statedir=/app/.tailscale --socket=/app/.tailscale/tailscaled.sock`
  2. `tailscale --socket=/app/.tailscale/tailscaled.sock up --authkey="$TS_AUTHKEY" --hostname=newsfoundry-backend`
  3. attend `BackendState=Running` (boucle sur `tailscale status --json`,
     avec timeout/erreur explicite si l'auth échoue)
  4. `exec python src/main.py`
- `CMD` → l'entrypoint.
- **Fallback dev/CI** : si `TS_AUTHKEY` est absent, skip Tailscale et lance
  l'app directement.

### 2. Modif code backend — factory client LLM partagée

`llm_provider.py:37` et `health_endpoints.py` construisent chacun un
`AsyncOpenAI`. Extraire une factory partagée (ex. `core/llm_client.py`) :

```python
def build_llm_client() -> AsyncOpenAI:
    proxy = os.getenv("LLM_PROXY_URL")  # ex. http://localhost:1055
    http_client = httpx.AsyncClient(proxy=proxy) if proxy else None
    return AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, http_client=http_client)
```

Les deux sites consomment cette factory. Quand `LLM_PROXY_URL` est vide
(dev/CI), `http_client=None` → comportement inchangé.

### 3. Config Railway + ACL Tailscale

- **Service backend Railway** :
  - `TS_AUTHKEY` (secret) — clé éphémère/reusable taggée
  - `LLM_PROXY_URL=http://localhost:1055`
  - `LLM_BASE_URL=http://100.70.22.24:30000/v1` (inchangé)
- **Console admin Tailscale** :
  - définir `tag:railway` (tagOwners)
  - règle ACL :
    `{"action":"accept","src":["tag:railway"],"dst":["100.70.22.24:30000"]}`
  - générer la clé éphémère/reusable avec `tag:railway`
- **Décommissionner** le service `railway-tailscale` (jayhale) + son volume.

## Flux d'erreur

- `TS_AUTHKEY` invalide/expirée → l'entrypoint échoue à l'étape 3 (timeout sur
  `BackendState=Running`) avec un log explicite ; le conteneur s'arrête (deploy
  Railway en échec visible) plutôt que de démarrer un backend sans LLM.
- vLLM injoignable malgré le tailnet → `/api/v1/health` renvoie `llm=error`
  (timeout 10s), `overall=error`, HTTP 503 — comportement #70 conservé.
- Dev local sans `TS_AUTHKEY` → app démarre sans proxy, appels LLM directs.

## Tests & vérification

- **Unit-test** de `build_llm_client` : proxy appliqué quand `LLM_PROXY_URL`
  est set, `http_client=None` sinon. Reste de la suite (LLM mocké) inchangé.
- **Post-deploy (manuel/wet-test)** : `tailscale status` montre le node
  `newsfoundry-backend` ; `GET /api/v1/health` → `overall=ok`,
  `subsystems.llm.status=ok`.

## Hors scope (suivi séparé)

- Le job `wet-test` garde un bug de **deploy race** : il tourne dès le push sur
  `main` alors que Railway déploie en asynchrone, donc il peut taper l'ancien
  déploiement. À corriger par un poll `/api/v1/health` avec retries (attente du
  déploiement) avant les assertions. Traité dans un travail dédié.
