# Design — RAG LlamaIndex pour la revue de presse

**Date :** 2026-06-14  
**Périmètre :** backend Python (FastAPI + OpenAI Agents SDK)  
**Objectif :** améliorer la revue de presse en ne référençant que les articles pertinents, grâce à un index vectoriel construit à partir des articles chargés durant le chat.

---

## Contexte

Actuellement, le `press_review_agent` reçoit uniquement l'historique conversationnel (titres + résumés retournés par les tools `get_top_news` et `search_news`). Il ne dispose d'aucun mécanisme de sélection sémantique : tous les articles mentionnés dans la conversation sont traités avec le même poids, qu'ils soient pertinents ou non.

La RAG (Retrieval Augmented Generation) permet de sélectionner, avant la génération, les articles les plus pertinents par rapport au contexte global du chat, et de n'injecter que ceux-là dans le prompt du `press_review_agent`.

---

## Architecture

### Flux global

```text
[Chat] → tool-call → articles collectés dans ChatRunContext
                                  ↓
                      saved as Chat.loaded_articles (JSON DB)
                                  ↓
[POST /chats/{id}/review] → charge loaded_articles
                                  ↓
                        LlamaIndex VectorIndex (in-memory)
                                  ↓
                   RAG query → top-k articles pertinents
                                  ↓
           press_review_agent enrichi → revue structurée
```

---

## Section 1 — Modèle de données

### Nouveau champ `Chat.loaded_articles`

- **Type :** `JSON` (liste de dicts)
- **Valeur par défaut :** `[]`
- **Structure d'un élément :**

  ```json
  {"title": "Titre de l'article", "summary": "Résumé 2-5 phrases.", "url": "https://..."}
  ```

- **Comportement :** les articles sont accumulés au fil des échanges du chat, dédupliqués par URL.

### Migration Alembic

Nouvelle révision : `add_loaded_articles_to_chat`

```sql
ALTER TABLE chat ADD COLUMN loaded_articles JSON NOT NULL DEFAULT '[]';
```

---

## Section 2 — Collecte des articles (`ChatRunContext`)

### Nouveau fichier `core/agent/context.py`

```python
from dataclasses import dataclass, field

@dataclass
class ChatRunContext:
    chat_id: int
    loaded_articles: list[dict] = field(default_factory=list)
```

### Refactoring des tools (`core/agent/tools.py`)

Chaque tool reçoit `ctx: RunContextWrapper[ChatRunContext]` en premier paramètre (convention Agents SDK). Les articles retournés par l'API sont ajoutés à `ctx.context.loaded_articles` avant le formatage Markdown.

- `search_news` : ajoute chaque `SearchArticle` (title, summary, url).
- `get_top_news` : ajoute le cluster représentatif (titre, résumé, top_url) pour chaque cluster retourné.

### Agent typé

```python
chat_agent = Agent[ChatRunContext](...)
```

### Intégration dans `_process_message()` (`api/chat_endpoints.py`)

```python
run_context = ChatRunContext(chat_id=chat_id)
result = await Runner.run(active_agent, input=openai_messages, context=run_context)

# Fusionner avec les articles existants (dédupliqués par URL)
# chat.loaded_articles est déjà une list Python (colonne JSON SQLAlchemy)
if run_context.loaded_articles:
    existing: list[dict] = chat.loaded_articles or []
    existing_urls = {a["url"] for a in existing}
    merged = existing + [a for a in run_context.loaded_articles if a["url"] not in existing_urls]
    await asyncio.to_thread(update_chat_loaded_articles_sync, chat_id, merged)
```

Nouvelle fonction CRUD : `update_chat_loaded_articles_sync(chat_id, articles: list[dict])`.

---

## Section 3 — Module RAG et enrichissement de la revue

### Nouveau module `core/rag/indexer.py`

Responsabilité unique : construire un index vectoriel en mémoire et retourner les top-k articles pertinents.

```python
from llama_index.core import VectorStoreIndex, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

_EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
_MAX_ARTICLES = 30  # plafond CPU — au-delà, l'indexation devient trop lente sur Railway

# Singleton : chargé une seule fois au démarrage du worker FastAPI
_embed = HuggingFaceEmbedding(model_name=_EMBED_MODEL)


def build_index_and_retrieve(
    articles: list[dict],
    query: str,
    top_k: int = 5,
) -> list[dict]:
    capped = articles[:_MAX_ARTICLES]
    docs = [
        Document(
            text=f"{a['title']}\n\n{a['summary']}",
            metadata={"title": a["title"], "url": a["url"]},
        )
        for a in capped
    ]
    index = VectorStoreIndex.from_documents(docs, embed_model=_embed)
    nodes = index.as_retriever(similarity_top_k=min(top_k, len(capped))).retrieve(query)
    return [
        {"title": n.metadata["title"], "summary": n.text, "url": n.metadata["url"]}
        for n in nodes
    ]
```

**Note :** l'index n'est pas persisté en base de données. Il est reconstruit à chaque appel de l'endpoint `/review`. Le plafond `_MAX_ARTICLES = 30` garantit un temps de réponse acceptable sur CPU sans GPU.

### Enrichissement dans `POST /chats/{id}/review` (`api/chat_endpoints.py`)

```python
relevant = []
articles: list[dict] = chat.loaded_articles or []  # JSON column — déjà désérialisé
if articles:
    # N'utiliser que les messages utilisateur récents pour la query RAG
    # (évite le bruit conversationnel des messages AI de transition)
    user_msgs = [m["content"] for m in llm_messages if m["role"] == "user"]
    query = " ".join(user_msgs[-3:])
    relevant = build_index_and_retrieve(articles, query, top_k=5)

if relevant:
    rag_block = "\n\n".join(
        f"**{a['title']}** ({a['url']})\n{a['summary']}" for a in relevant
    )
    llm_messages = [
        {"role": "system", "content": f"Articles pertinents identifiés :\n\n{rag_block}"},
        *llm_messages,
    ]
```

### Dépendances (`pyproject.toml`)

```toml
"llama-index-core>=0.12",
"llama-index-embeddings-huggingface>=0.4",
```

Le modèle `paraphrase-multilingual-MiniLM-L12-v2` (~120 Mo) est téléchargé automatiquement par HuggingFace au premier usage et mis en cache dans `~/.cache/huggingface/`.

---

## Déploiement Railway — contraintes

Le container Railway est éphémère et l'utilisateur `appuser` est créé avec `--no-create-home`. Deux adaptations obligatoires dans le `Dockerfile` :

1. **Pré-télécharger le modèle au build** (évite un re-download de 120 Mo à chaque démarrage) :

   ```dockerfile
   ENV HF_HOME=/app/.hf_cache
   RUN python -c "from llama_index.embeddings.huggingface import HuggingFaceEmbedding; \
       HuggingFaceEmbedding(model_name='paraphrase-multilingual-MiniLM-L12-v2')"
   ```

2. **Définir `HF_HOME`** vers un chemin accessible à `appuser` (pas de home dir) — `/app/.hf_cache` est dans le workdir de l'app, toujours accessible.

3. **RAM** : le modèle consomme ~300 Mo en mémoire résidente. Le plan Railway Hobby (8 Go RAM par replica) offre largement assez de marge — aucune contrainte mémoire.

---

## Tests

- **Unitaire `core/rag/indexer.py`** : vérifier que `build_index_and_retrieve` retourne les articles les plus proches d'une requête test.
- **Unitaire tools** : vérifier que `ctx.context.loaded_articles` est bien rempli après un appel à `search_news` ou `get_top_news` (mock de l'API WorldNews).
- **Intégration** : vérifier que `POST /chats/{id}/review` retourne uniquement des articles dont les URLs sont dans `loaded_articles`.

---

## Fichiers impactés

| Fichier | Changement |
| --- | --- |
| `src/database/models.py` | + champ `loaded_articles` sur `Chat` |
| `alembic/versions/XXX_add_loaded_articles_to_chat.py` | Nouvelle migration |
| `src/database/crud.py` | + `update_chat_loaded_articles_sync` |
| `src/core/agent/context.py` | Nouveau — `ChatRunContext` |
| `src/core/agent/tools.py` | Refactoring — `ctx` en 1er arg |
| `src/core/agent/search_agent.py` | `Agent[ChatRunContext]` |
| `src/core/rag/__init__.py` | Nouveau (vide) |
| `src/core/rag/indexer.py` | Nouveau — `build_index_and_retrieve` |
| `src/api/chat_endpoints.py` | + création `ChatRunContext`, sauvegarde articles, RAG au moment review |
| `pyproject.toml` | + `llama-index-core`, `llama-index-embeddings-huggingface` |
