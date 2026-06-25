# Design : Enrichissement des traces Phoenix et évaluation NewsFoundry

**Date** : 2026-06-25  
**Projet** : NewsFoundry backend  
**Phoenix** : 17.10.0 (self-hosted VPS `phoenix.willisback.fr`)

---

## Contexte

Le backend NewsFoundry envoie déjà des spans vers Phoenix via OTelCollector :
- Spans agent/tool/LLM auto-instrumentés par `openinference-instrumentation-openai-agents`
- Spans HTTP FastAPI via `opentelemetry-instrumentation-fastapi`

Deux flux LLM ne sont pas encore tracés dans Phoenix :
1. **RAG** : `build_index_and_retrieve()` est une boîte noire, aucun span
2. **Revue de presse** : le span agent existe mais sans les articles sources en attributs

Aucun système d'évaluation n'est en place.

---

## Objectif

1. Enrichir les traces Phoenix avec des spans dédiés au RAG et à la génération de revue de presse
2. Mettre en place l'évaluation via les **Experiments Phoenix** (LLM-as-judge + CODE) sans modifier le pipeline de prod

---

## Périmètre d'évaluation

| Composant | Métrique | Type |
|-----------|----------|------|
| RAG | Pertinence des articles récupérés vs query | LLM-as-judge |
| RAG | Couverture (`retrieved_count / top_k`) | CODE |
| Revue de presse | Fidélité aux sources (hallucination ?) | LLM-as-judge |
| Revue de presse | Qualité rédactionnelle (cohérence, structure) | LLM-as-judge |

---

## Architecture

### Flux de données

```
generate_chat_review()
├── [SPAN RETRIEVER] build_index_and_retrieve()
│     ├── input.value = query
│     ├── retrieval.documents.N.* = articles retournés
│     ├── rag.top_k = 5
│     └── rag.retrieved_count = nb résultats
│
└── [SPAN CHAIN] press_review_generation
      ├── input.value = articles sources (titres + URLs)
      ├── output.value = review (title + editorial)
      ├── chat.articles_count = len(all_articles)
      └── [enfants auto-instrumentés par SDK]
            ├── AgentSpan
            ├── GenerationSpan (LLM)
            └── FunctionSpan (tools)
```

### Évaluation (Phoenix Experiments)

Aucun code d'évaluation dans le backend. Tout se passe dans Phoenix :

1. **Dataset** : créé dans l'UI Phoenix depuis les spans RETRIEVER et CHAIN
2. **Judge model** : `OpenAIModel` configuré avec l'IP publique DGX Spark + API key (vLLM Qwen3-35B)
3. **Experiments** : lancés manuellement depuis Phoenix sur les datasets

---

## Composants à modifier

### `src/core/observability.py`

Ajouter un `tracer` OTel et deux context managers :

```python
from opentelemetry import trace

_tracer = trace.get_tracer("newsfoundry")

@contextmanager
def rag_span(query: str, top_k: int):
    """Span RETRIEVER OpenInference autour du RAG."""
    with _tracer.start_as_current_span("rag_retrieve") as span:
        span.set_attribute("openinference.span.kind", "RETRIEVER")
        span.set_attribute("input.value", query)
        span.set_attribute("rag.top_k", top_k)
        yield span

@contextmanager
def press_review_span(articles: list[dict]):
    """Span CHAIN OpenInference autour de la génération de revue de presse."""
    with _tracer.start_as_current_span("press_review_generation") as span:
        span.set_attribute("openinference.span.kind", "CHAIN")
        sources = [{"title": a.get("title",""), "url": a.get("url","")} for a in articles]
        span.set_attribute("input.value", json.dumps(sources, ensure_ascii=False))
        yield span
```

### `src/api/chat_endpoints.py`

**Dans `generate_chat_review()`** :

Envelopper `build_index_and_retrieve` dans `rag_span()` :
```python
with rag_span(query=query, top_k=5) as rspan:
    relevant = await asyncio.to_thread(build_index_and_retrieve, articles, query, top_k=5)
    # Ajouter les documents récupérés en attributs
    for i, a in enumerate(relevant):
        rspan.set_attribute(f"retrieval.documents.{i}.document.content", a.get("summary", ""))
        rspan.set_attribute(f"retrieval.documents.{i}.document.metadata.url", a.get("url", ""))
        rspan.set_attribute(f"retrieval.documents.{i}.document.metadata.title", a.get("title", ""))
    rspan.set_attribute("rag.retrieved_count", len(relevant))
```

Envelopper `Runner.run(press_review_agent)` dans `press_review_span()` :
```python
with press_review_span(articles=all_articles) as prspan:
    result = await asyncio.wait_for(
        Runner.run(active_review_agent, input=llm_messages),
        timeout=LLM_TIMEOUT_SECONDS,
    )
    if result.final_output:
        prspan.set_attribute("output.value", result.final_output.title + " — " + result.final_output.editorial[:200])
        prspan.set_attribute("chat.articles_count", len(all_articles))
```

---

## Configuration Phoenix Experiments (VPS)

### Judge model

Dans Phoenix UI → Settings → Models :
```
Provider : OpenAI-compatible
Base URL : http://<DGX_PUBLIC_IP>:<PORT>/v1
API Key  : <DGX_API_KEY>
Model    : <LLM_MODEL>
Max tokens : 256  (réponses courtes pour scoring)
```

### Prompts LLM-as-judge

**RAG Pertinence** :
```
Tu es un évaluateur de pertinence. 
Query : {query}
Articles récupérés : {retrieval.documents}
Les articles récupérés sont-ils pertinents par rapport à la query ?
Réponds : "relevant" (score 1.0), "partially_relevant" (score 0.5), ou "irrelevant" (score 0.0).
Explique brièvement.
```

**Fidélité revue de presse** :
```
Tu es un fact-checker.
Articles sources : {input.value}
Revue générée : {output.value}
La revue contient-elle des affirmations absentes des sources (hallucinations) ?
Réponds : "faithful" (score 1.0), "partially_faithful" (score 0.5), ou "hallucinated" (score 0.0).
Explique brièvement.
```

**Qualité rédactionnelle** :
```
Tu es un éditeur de presse.
Revue générée : {output.value}
La revue est-elle cohérente, bien structurée et analytiquement pertinente ?
Réponds : "high_quality" (score 1.0), "acceptable" (score 0.5), ou "poor" (score 0.0).
Explique brièvement.
```

### Evaluator CODE — couverture RAG

```python
def rag_coverage(retrieved_count: int, top_k: int) -> float:
    return retrieved_count / top_k if top_k > 0 else 0.0
```

---

## Dépendances backend

Aucune nouvelle dépendance — le tracer OTel est déjà configuré dans `telemetry.py`.

---

## Contraintes

- **Zéro impact latence** : pas d'évaluation en ligne, les experiments sont lancés manuellement dans Phoenix
- **Zéro ouverture de port** : l'évaluation tourne entièrement dans Phoenix sur le VPS
- **vLLM accessible depuis le VPS** : Phoenix → IP publique DGX Spark (confirmé)
- **Pas de nouvelles dépendances Python** dans le backend

---

## Fichiers modifiés

| Fichier | Changement |
|---------|------------|
| `backend/src/core/observability.py` | Ajout `rag_span()` et `press_review_span()` |
| `backend/src/api/chat_endpoints.py` | Utilisation des deux nouveaux context managers |

---

## Hors périmètre

- Évaluation automatique en ligne (fire-and-forget)
- Annotation programmatique via l'API Phoenix REST depuis Railway
- Modification de `search_agent.py` ou `press_review_agent.py`
