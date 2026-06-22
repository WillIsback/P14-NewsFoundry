# Spec : Observabilité LLM — Instrumentation des latences + MLflow

**Date :** 2026-06-22
**Branche :** `feat/observability-mlflow-latency-tracking`
**Issue :** [#182](https://github.com/WillIsback/P14-NewsFoundry/issues/182)

---

## Contexte et objectif

Le pipeline d'inférence de NewsFoundry n'est actuellement pas instrumenté : aucun timing sur `call_llm`, aucun log des tokens consommés, latence des tool calls WorldNewsAPI invisible. L'objectif est de mettre en place une instrumentation de base qui :

1. Traque automatiquement chaque opération métier en production
2. Persiste les métriques dans MLflow (service Railway)
3. Fournit des données réelles pour alimenter le document de performance OpenClassrooms

---

## Architecture générale

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI endpoint  (chat_endpoints.py)                   │
│                                                          │
│  1. InferenceTrace.start("chat_turn" | "review")        │
│  2. Runner.run(chat_agent | press_review_agent)          │
│     ├── call_llm / call_llm_structured                   │
│     │     └── trace.record_llm(tokens, duration)        │
│     └── get_top_news / search_news                       │
│           └── trace.record_tool(name, duration)          │
│  3. trace.flush() → MLflow run                           │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  MLflow (service Railway)               │
│  • tracking URI : http://mlflow:5000    │
│  • backend : SQLite sur volume Railway  │
│  • 2 experiment types :                 │
│    - "newsfoundry/chat_turn"            │
│    - "newsfoundry/press_review"         │
└─────────────────────────────────────────┘
```

**Nouveau fichier :** `backend/src/core/observability.py` — seul module qui importe `mlflow`. Aucun autre fichier ne dépend de MLflow directement.

**Dégradation gracieuse :** si `MLFLOW_TRACKING_URI` n'est pas défini, tout le tracking est en mode no-op silencieux. Le backend reste fonctionnel sans MLflow.

---

## Métriques capturées

### Run `newsfoundry/chat_turn`

Déclenché à chaque message utilisateur traité par le `chat_agent`.

| Métrique | Type | Description |
|---|---|---|
| `e2e_latency_s` | float | Durée totale du tour (endpoint complet) |
| `llm_calls_count` | int | Nombre d'appels LLM dans le tour (typiquement 2 : décision + réponse) |
| `input_tokens_total` | int | Tokens d'entrée cumulés sur tous les appels LLM |
| `output_tokens_total` | int | Tokens de sortie cumulés |
| `tok_per_sec` | float | `output_tokens_total / llm_duration_total_s` |
| `tool_calls_count` | int | Nombre d'appels tool (0, 1 ou 2) |
| `tool_latency_s` | float | Durée cumulée des tool calls WorldNewsAPI |
| `was_compacted` | int (0/1) | Compaction de l'historique déclenchée |
| `history_length` | int | Nombre de messages dans l'historique avant le tour |

**Tags MLflow :** `chat_id`, `model` (nom du LLM retourné par vLLM)

### Run `newsfoundry/press_review`

Déclenché à chaque génération de revue de presse via `press_review_agent`.

| Métrique | Type | Description |
|---|---|---|
| `e2e_latency_s` | float | Durée totale de génération |
| `input_tokens` | int | Tokens d'entrée (historique + articles chargés) |
| `output_tokens` | int | Tokens de sortie (revue structurée) |
| `tok_per_sec` | float | Throughput de génération |
| `articles_count` | int | Nombre d'articles dans le contexte |

**Tags MLflow :** `chat_id`, `model`

---

## `InferenceTrace` — design détaillé

**Fichier :** `backend/src/core/observability.py`

```
InferenceTrace
├── start(operation: Literal["chat_turn", "review"]) → ContextVar set
├── record_llm(input_tokens, output_tokens, duration_s, model)
├── record_tool(tool_name, duration_s)
├── record_compaction(was_compacted, history_length)
└── flush(chat_id) → mlflow.start_run() + log_metrics() + log_params()
```

La propagation par `contextvars.ContextVar` isole automatiquement les traces entre coroutines concurrentes — pas de race condition avec des requêtes parallèles.

**Pattern no-op :** si la `ContextVar` n'a pas de trace active, tous les `record_*` retournent immédiatement sans erreur ni exception.

---

## Points d'injection dans le code existant

Modifications minimales — la logique métier est préservée à l'identique.

| Fichier | Ligne | Modification |
|---|---|---|
| `backend/src/core/llm_provider.py` | L.101 | `call_llm` appelle `trace.record_llm(...)` après `wait_for(...)` |
| `backend/src/core/llm_provider.py` | L.141 | `call_llm_structured` appelle `trace.record_llm(...)` après `wait_for(...)` |
| `backend/src/core/llm_provider.py` | L.208 | `compact_history_if_needed` appelle `trace.record_compaction(...)` |
| `backend/src/core/agent/tools.py` | L.27 | `get_top_news` appelle `trace.record_tool(...)` |
| `backend/src/core/agent/tools.py` | L.96 | `search_news` appelle `trace.record_tool(...)` |
| `backend/src/api/chat_endpoints.py` | endpoint chat | `trace.start()` + `trace.flush()` en try/finally |
| `backend/src/api/chat_endpoints.py` | endpoint review | idem |
| `backend/src/core/config.py` | — | Ajout de `MLFLOW_TRACKING_URI` (optionnel, défaut `None`) |

---

## Infrastructure MLflow sur Railway

**Service dédié dans le projet Railway :**

```
Image    : ghcr.io/mlflow/mlflow:latest
Commande : mlflow server
             --host 0.0.0.0
             --port 5000
             --backend-store-uri sqlite:////mlflow/mlruns.db
             --default-artifact-root /mlflow/artifacts
Volume   : /mlflow (volume Railway persistant)
```

**Variable d'env ajoutée au service backend Railway :**
```
MLFLOW_TRACKING_URI=http://mlflow.railway.internal:5000
```
> Note : le nom `mlflow` est le nom du service Railway à définir lors du déploiement — Railway résout automatiquement les noms de services sur le réseau interne.

---

## Gestion d'erreurs et dégradation gracieuse

| Scénario | Comportement |
|---|---|
| `MLFLOW_TRACKING_URI` absent | `InferenceTrace` en mode no-op, zéro overhead |
| Service MLflow Railway down | Warning loggé, requête utilisateur non affectée |
| Timeout MLflow | `flush()` abandonne après 2s, silencieusement |
| `record_llm()` hors endpoint | No-op (pas de `ContextVar` active) |

**Pattern dans `flush()` :**

```python
try:
    mlflow.start_run(...)
    mlflow.log_metrics(...)
except Exception as e:
    logger.warning("[observability] MLflow flush failed", error=str(e))
# La réponse utilisateur est déjà partie — le try/finally garantit ça
```

---

## Logs structurés Railway (indépendants de MLflow)

En parallèle du tracking MLflow, chaque `record_llm` émet un log JSON via le logger existant. Ces logs remontent dans Railway sans aucune dépendance au service MLflow :

```json
{"event": "llm_call", "duration_s": 4.2, "input_tokens": 1820,
 "output_tokens": 312, "tok_per_sec": 74.3, "model": "qwen3-8b"}
```

```json
{"event": "tool_call", "tool": "get_top_news", "duration_s": 3.1}
```

```json
{"event": "chat_turn_complete", "e2e_latency_s": 8.7,
 "llm_calls": 2, "tool_calls": 1, "was_compacted": false}
```

---

## Hors périmètre

- Streaming SSE (TTFT) — chantier séparé
- MLflow Model Registry — pas de modèle custom à versionner
- Alerting automatique sur seuils — pas prévu
- Dashboard custom — l'UI MLflow native suffit
