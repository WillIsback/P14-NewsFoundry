# Phoenix Evaluation Workflow — Design Spec

**Date:** 2026-06-25
**Statut:** Approuvé

---

## Contexte

NewsFoundry utilise un LLM en mode agent (openai-agents SDK) avec deux agents :

- **`search_agent`** : agent conversationnel avec deux tools (`get_top_news`, `search_news`)
- **`press_review_agent`** : génération d'éditorial structuré (zéro tool, structured output)

Phoenix self-hosted reçoit déjà les spans OpenInference du backend Railway via OTel Collector. Les spans couvrent les types : `AGENT`, `TOOL`, `RETRIEVER` (rag_span), `LLM`.

**Problème :** aucune évaluation qualitative n'existe. Les métriques actuelles sont purement techniques (latence, tokens, throughput). On ne sait pas si les inférences sont bonnes ou mauvaises.

**Objectif :** ajouter un workflow d'évaluation asynchrone post-inférence qui score chaque trace selon trois étapes du pipeline agent, et annote les résultats directement dans Phoenix pour constituer un dataset de bonnes/mauvaises inférences.

---

## Architecture générale

```
Backend Railway (FastAPI)
    │
    │  OTEL spans OpenInference → https://otelcol.willisback.fr (basic auth)
    ▼
OTel Collector (VPS Docker) → Phoenix (VPS Docker, http://phoenix:6006)
                                      │
                                      │  px.Client() — réseau Docker will-vps-net
                                      ▼
                            ┌──────────────────────────┐
                            │   eval-worker (VPS)      │
                            │                          │
                            │  1. Fetch spans Phoenix  │
                            │  2. Règles  (étapes 1+2) │
                            │  3. LLM-judge (étape 3)  │
                            │  4. log_evaluations()    │
                            └──────────────────────────┘
                                      │
                            cron VPS (crontab, toutes les 30 min)
                            → docker compose run --rm eval-worker
```

**Principes clés :**
- L'eval-worker tourne **sur le VPS** dans le réseau Docker `will-vps-net` → accès direct à `http://phoenix:6006` sans auth
- Déclenchement par **cron système VPS** (pas Railway), `*/30 * * * *`
- Le worker est **éphémère** (`restart: no`, profile Docker `eval`) — lance, évalue, se termine
- Le backend Railway n'est **pas modifié** — les spans existants suffisent
- Les annotations sont stockées dans **Phoenix** (dataset intégré à l'UI)

---

## Pipeline d'évaluation

Les spans OpenInference disponibles dans Phoenix :

| `openinference.span.kind` | Source | Contient |
|---|---|---|
| `AGENT` | openai-agents instrumentor | session complète, input utilisateur |
| `TOOL` | openai-agents instrumentor | tool name, input, output, durée |
| `RETRIEVER` | `rag_span()` custom | query, top_k, documents récupérés |
| `LLM` | openai-agents instrumentor | prompt complet, completion, tokens |

### Étape 1 — Sélection d'outil (règles, spans TOOL)

**Évaluateur :** `tool_evaluator.py`

- **`tool_used`** (binaire) : l'agent a-t-il appelé au moins un outil dans la session ?
  - Score `1.0` / label `used` si au moins 1 span TOOL présent
  - Score `0.0` / label `missing` sinon

- **`tool_relevance`** (0→1) : le bon outil a-t-il été sélectionné ?
  - Heuristique : `search_news` attendu si la query contient une entité précise (nom propre, pays, sujet spécifique)
  - `get_top_news` attendu pour queries génériques ("actualités", "news", "quoi de neuf")
  - Score `1.0` / label `relevant` si correspondance, `0.0` / label `wrong_tool` sinon

### Étape 2 — Qualité retrieval (règles, spans RETRIEVER)

**Évaluateur :** `retrieval_evaluator.py`

- **`retrieval_coverage`** (0→1) : `retrieved_count / top_k`
  - Détecte les cas où l'API news a retourné moins de résultats qu'attendu

- **`retrieval_overlap`** (0→1) : overlap lexical Jaccard entre tokens de la query et tokens des titres d'articles retournés
  - Mesure la pertinence thématique des documents récupérés sans LLM

### Étape 3 — Qualité génération (LLM-as-judge, spans LLM)

**Évaluateur :** `generation_evaluator.py`

Utilise les templates natifs `arize-phoenix-evals` :

- **`relevance`** (score 1→4) : la réponse répond-elle à la question posée ?
  - Template `RelevanceEvaluator` (Phoenix natif)
  - Label : `relevant` / `irrelevant`

- **`hallucination`** : la réponse invente-t-elle des faits absents des articles sources ?
  - Template `HallucinationEvaluator` (Phoenix natif)
  - Label : `factual` / `hallucinated`

Le juge appelle `EVAL_LLM_BASE_URL` (OpenAI-compatible). Le VPS OVH n'est **pas sur le tailnet Tailscale** (Tailscale est embarqué dans le conteneur Railway uniquement) — le vLLM privé (`100.70.22.24:30000`) n'est donc pas joignable depuis le VPS.

**Option retenue : Tailscale sur le VPS OVH avec ACL restreinte.**

Le VPS rejoint le tailnet avec le tag `tag:vps`. Les ACL Tailscale (mode `grants`) limitent sa visibilité au GB10 uniquement — les PC perso ne sont pas accessibles depuis le VPS.

**Config ACL Tailscale à appliquer :**
```json
{
  "tagOwners": {
    "tag:railway": ["autogroup:admin"],
    "tag:vps":     ["autogroup:admin"]
  },
  "grants": [
    {
      "src": ["tag:railway"],
      "dst": ["tag:gpu"],
      "ip":  ["*"]
    },
    {
      "src": ["tag:vps"],
      "dst": ["tag:gpu"],
      "ip":  ["30000"]
    }
  ]
}
```

- Le GB10/spark-787d-1 doit porter le tag `tag:gpu`
- `tag:vps` ne peut atteindre que le port `30000` du GB10 — aucun accès aux machines perso
- `EVAL_LLM_BASE_URL=http://100.70.22.24:30000/v1` (même IP Tailscale que le backend Railway)

---

## Structure des fichiers

### Sur le VPS (`~/infra/stacks/monitoring/`)

```
monitoring/
├── docker-compose.yml          ← ajout service eval-worker
└── eval/
    ├── Dockerfile
    ├── requirements.txt
    ├── eval_worker.py           ← point d'entrée principal
    ├── config.py                ← variables d'environnement
    └── evaluators/
        ├── __init__.py
        ├── tool_evaluator.py
        ├── retrieval_evaluator.py
        └── generation_evaluator.py
```

### Dans le repo NewsFoundry (documentation uniquement)

```
docs/
└── superpowers/
    └── specs/
        └── 2026-06-25-phoenix-evaluation-workflow-design.md  ← ce fichier
```

---

## Configuration Docker

### Ajout dans `docker-compose.yml`

```yaml
eval-worker:
  build: ./eval
  container_name: eval-worker
  networks: [will-vps-net]
  environment:
    PHOENIX_ENDPOINT: "http://phoenix:6006"
    PHOENIX_PROJECT_NAME: "newsfoundry"
    EVAL_LLM_BASE_URL: "${EVAL_LLM_BASE_URL}"
    EVAL_LLM_MODEL: "${EVAL_LLM_MODEL}"
    EVAL_LOOKBACK_MINUTES: "60"
  profiles: ["eval"]
  restart: "no"
```

### Cron VPS (`crontab -e` pour ubuntu)

```bash
*/30 * * * * cd /home/ubuntu/infra/stacks/monitoring && \
  docker compose --profile eval run --rm eval-worker \
  >> /var/log/eval-worker.log 2>&1
```

---

## Logique `eval_worker.py`

```
1. Connexion : px.Client(endpoint=PHOENIX_ENDPOINT)
2. Fetch : get_spans_dataframe(project=PHOENIX_PROJECT_NAME)
3. Filtre : spans des EVAL_LOOKBACK_MINUTES dernières minutes
4. Déduplication : skip les span_id déjà annotés (vérif via px.get_evaluations())
5. Groupement : agréger spans par trace_id (AGENT parent + enfants TOOL/RETRIEVER/LLM)
6. Éval étape 1 : tool_evaluator.evaluate(agent_spans, tool_spans)
7. Éval étape 2 : retrieval_evaluator.evaluate(retriever_spans)
8. Éval étape 3 : generation_evaluator.evaluate(llm_spans)
9. Post : px.Client().log_evaluations([...tous résultats...])
10. Log : "Évalué N traces — relevance moy: X.X, hallucination: Y%"
```

---

## Annotations dans Phoenix

| Eval name | Span ciblé | Type valeur | Labels |
|---|---|---|---|
| `tool_used` | AGENT | binaire 0/1 | `used` / `missing` |
| `tool_relevance` | TOOL | float 0→1 | `relevant` / `wrong_tool` |
| `retrieval_coverage` | RETRIEVER | float 0→1 | — |
| `retrieval_overlap` | RETRIEVER | float 0→1 | — |
| `relevance` | LLM | int 1→4 | `relevant` / `irrelevant` |
| `hallucination` | LLM | — | `factual` / `hallucinated` |

Les traces annotées deviennent un dataset dans Phoenix consultable via **Datasets & Experiments**.

---

## Dépendances Python (`requirements.txt`)

```
arize-phoenix>=4.0.0
arize-phoenix-evals>=0.17.0
pandas>=2.0.0
openai>=1.0.0          # client OpenAI-compatible pour LLM judge
```

---

## Variables d'environnement

| Variable | Description | Exemple |
|---|---|---|
| `PHOENIX_ENDPOINT` | URL interne Phoenix | `http://phoenix:6006` |
| `PHOENIX_PROJECT_NAME` | Nom projet dans Phoenix | `newsfoundry` |
| `EVAL_LLM_BASE_URL` | Endpoint LLM judge (OpenAI-compatible) | `http://100.70.22.24:30000/v1` |
| `EVAL_LLM_MODEL` | Modèle à utiliser comme juge | `Qwen/Qwen3-35B-A22B` |
| `EVAL_LOOKBACK_MINUTES` | Fenêtre de temps pour fetch spans | `60` |

---

## Ce qui n'est PAS inclus dans ce scope

- Modification du backend Railway (aucune)
- Interface utilisateur de review manuelle (Phoenix UI suffit)
- Fine-tuning à partir du dataset (étape future)
- Évaluation en temps réel / inline (choix délibéré : asynchrone uniquement)
- Alerting sur seuils de scores (étape future)
