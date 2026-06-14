# RAG LlamaIndex — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrichir la revue de presse avec un index vectoriel LlamaIndex construit à partir des articles collectés lors du chat, pour ne générer une revue qu'avec les articles sémantiquement pertinents.

**Architecture:** Les tools `search_news` et `get_top_news` reçoivent un `ChatRunContext` via le mécanisme `TContext` du SDK Agents et y accumulent les articles trouvés. Après chaque run, les articles sont persistés dans `Chat.loaded_articles` (colonne JSON). Lors de `POST /chats/{id}/review`, un index LlamaIndex en mémoire est construit, interrogé avec les derniers messages utilisateur, et les top-5 articles pertinents sont injectés dans le prompt du `press_review_agent`.

**Tech Stack:** FastAPI, OpenAI Agents SDK, SQLModel/PostgreSQL, LlamaIndex Core, `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace, CPU)

**Spec:** `docs/specs/2026-06-14-rag-llamaindex-design.md`

---

## Cartographie des fichiers

| Fichier | Action | Responsabilité |
| --- | --- | --- |
| `backend/pyproject.toml` | Modifier | Ajouter dépendances llama-index |
| `backend/src/database/models.py` | Modifier | + champ `loaded_articles: list` sur `Chat` |
| `backend/alembic/versions/YYYYMMDD_add_loaded_articles_to_chat.py` | Créer | Migration SQL — ADD COLUMN |
| `backend/src/database/crud.py` | Modifier | + `update_chat_loaded_articles[_sync]` |
| `backend/src/core/agent/context.py` | Créer | Dataclass `ChatRunContext` |
| `backend/src/core/agent/tools.py` | Modifier | Ajouter `ctx` en 1er arg des tools |
| `backend/src/core/agent/search_agent.py` | Modifier | Typer `Agent[ChatRunContext]` |
| `backend/src/core/rag/__init__.py` | Créer | Package marker (vide) |
| `backend/src/core/rag/indexer.py` | Créer | Singleton embed + `build_index_and_retrieve` |
| `backend/src/api/chat_endpoints.py` | Modifier | Créer `ChatRunContext`, sauvegarder articles, enrichir review |
| `backend/Dockerfile` | Modifier | `ENV HF_HOME`, pré-téléchargement modèle |
| `backend/tests/test_agent_tools.py` | Modifier | Tests de collecte articles dans context |
| `backend/tests/test_rag_indexer.py` | Créer | Tests unitaires `build_index_and_retrieve` |

---

## Task 1 : Dépendances LlamaIndex

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1 : Ajouter les dépendances**

Dans `backend/pyproject.toml`, ajouter dans le bloc `dependencies` :

```toml
dependencies = [
    ...
    "llama-index-core>=0.12",
    "llama-index-embeddings-huggingface>=0.4",
]
```

- [ ] **Step 2 : Synchroniser l'environnement**

```bash
cd backend
uv sync
```

Résultat attendu : pas d'erreur, packages résolus et installés.

- [ ] **Step 3 : Vérifier les imports**

```bash
uv run python -c "from llama_index.core import VectorStoreIndex, Document; from llama_index.embeddings.huggingface import HuggingFaceEmbedding; print('OK')"
```

Résultat attendu : `OK`

- [ ] **Step 4 : Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore: add llama-index-core and llama-index-embeddings-huggingface"
```

---

## Task 2 : Modèle de données + migration Alembic

**Files:**
- Modify: `backend/src/database/models.py`
- Create: `backend/alembic/versions/YYYYMMDD_add_loaded_articles_to_chat.py`

- [ ] **Step 1 : Ajouter `loaded_articles` au modèle `Chat`**

Dans `backend/src/database/models.py`, modifier la classe `Chat` :

```python
from sqlalchemy import JSON, Column  # déjà importé en haut du fichier

class Chat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: str = Field(default=None)
    system_prompt: Optional[str] = Field(default=None)
    press_review_title: Optional[str] = Field(default=None)
    press_review_summary: Optional[str] = Field(default=None)
    press_review_articles: Optional[str] = Field(default=None)
    press_review_date: Optional[str] = Field(default=None)
    loaded_articles: list = Field(default=[], sa_column=Column(JSON, nullable=False, server_default="[]"))
    messages: list[Message] = Relationship()
    top_news_context: Optional["TopNewsContext"] = Relationship()
```

- [ ] **Step 2 : Générer la migration Alembic**

```bash
cd backend
uv run alembic revision --autogenerate -m "add_loaded_articles_to_chat"
```

Résultat attendu : un nouveau fichier `alembic/versions/XXXX_add_loaded_articles_to_chat.py` créé.

- [ ] **Step 3 : Vérifier et corriger la migration générée**

Ouvrir le fichier généré et s'assurer que `upgrade()` contient bien :

```python
def upgrade() -> None:
    op.add_column(
        "chat",
        sa.Column("loaded_articles", sa.JSON(), nullable=False, server_default="[]"),
    )

def downgrade() -> None:
    op.drop_column("chat", "loaded_articles")
```

Si `autogenerate` n'a pas détecté la colonne (cas possible avec `sa_column`), écrire manuellement le fichier avec ce contenu, en mettant à jour `revision` et `down_revision` pour chaîner correctement après la dernière migration (`a1b2c3d4e5f6`).

- [ ] **Step 4 : Appliquer la migration (base locale si disponible, sinon skip)**

```bash
uv run alembic upgrade head
```

- [ ] **Step 5 : Commit**

```bash
git add backend/src/database/models.py backend/alembic/versions/
git commit -m "feat: add loaded_articles JSON column to Chat model"
```

---

## Task 3 : `ChatRunContext` + fonction CRUD

**Files:**
- Create: `backend/src/core/agent/context.py`
- Modify: `backend/src/database/crud.py`

- [ ] **Step 1 : Créer `core/agent/context.py`**

```python
# backend/src/core/agent/context.py
from dataclasses import dataclass, field


@dataclass
class ChatRunContext:
    chat_id: int
    loaded_articles: list[dict] = field(default_factory=list)
```

- [ ] **Step 2 : Ajouter les fonctions CRUD dans `crud.py`**

À la fin de `backend/src/database/crud.py`, après `update_chat_press_review_sync`, ajouter :

```python
def update_chat_loaded_articles(
    session: Session, chat_id: int, articles: list
) -> None:
    chat = session.get(Chat, chat_id)
    if not chat:
        logger.warning("Chat %s not found for loaded_articles update", chat_id)
        return
    chat.loaded_articles = articles
    session.add(chat)
    session.commit()


def update_chat_loaded_articles_sync(chat_id: int, articles: list) -> None:
    with Session(engine) as session:
        update_chat_loaded_articles(session, chat_id, articles)
```

- [ ] **Step 3 : Vérifier que les tests existants passent toujours**

```bash
cd backend
uv run pytest tests/ -x -q
```

Résultat attendu : tous les tests passent (aucun test ne valide ces nouvelles fonctions directement — elles seront couvertes par les tests des tasks suivantes).

- [ ] **Step 4 : Commit**

```bash
git add backend/src/core/agent/context.py backend/src/database/crud.py
git commit -m "feat: add ChatRunContext dataclass and update_chat_loaded_articles CRUD"
```

---

## Task 4 : Refactoring des tools avec `ChatRunContext`

**Files:**
- Modify: `backend/src/core/agent/tools.py`
- Modify: `backend/src/core/agent/search_agent.py`
- Modify: `backend/tests/test_agent_tools.py`

- [ ] **Step 1 : Écrire les tests qui vont échouer**

Dans `backend/tests/test_agent_tools.py`, remplacer `_make_run_ctx` par une version qui inclut un vrai `ChatRunContext`, et ajouter deux nouveaux tests :

```python
def _make_run_ctx(chat_id: int = 1) -> MagicMock:
    """Construit un RunContextWrapper avec un vrai ChatRunContext."""
    from core.agent.context import ChatRunContext
    ctx = MagicMock()
    ctx.run_config = MagicMock()
    ctx.run_config.model_settings = None
    ctx.context = ChatRunContext(chat_id=chat_id)
    return ctx
```

Puis ajouter dans `TestSearchNewsTool` :

```python
@pytest.mark.asyncio
async def test_search_news_populates_loaded_articles(self):
    from core.news.search import SearchArticle
    mock_articles = [
        SearchArticle(
            title="IA en France",
            url="https://example.com/ia",
            summary="OpenAI sort un nouveau modèle.",
            publish_date="2026-06-14",
        )
    ]
    ctx = _make_run_ctx()
    with patch("core.agent.tools._search_news", return_value=mock_articles):
        from core.agent.tools import search_news
        await search_news.on_invoke_tool(
            ctx, '{"query":"IA","language":"fr","max_results":5}'
        )
    assert len(ctx.context.loaded_articles) == 1
    assert ctx.context.loaded_articles[0]["url"] == "https://example.com/ia"
    assert ctx.context.loaded_articles[0]["title"] == "IA en France"
    assert "OpenAI" in ctx.context.loaded_articles[0]["summary"]
```

Et dans `TestGetTopNewsTool` :

```python
@pytest.mark.asyncio
async def test_get_top_news_populates_loaded_articles(self, mock_api):
    ctx = _make_run_ctx()
    with patch("core.agent.tools.get_news_api", return_value=mock_api):
        from core.agent.tools import get_top_news
        await get_top_news.on_invoke_tool(
            ctx, '{"source_country":"fr","language":"fr"}'
        )
    # 3 clusters dans _make_top_news_response(3)
    assert len(ctx.context.loaded_articles) == 3
    urls = [a["url"] for a in ctx.context.loaded_articles]
    assert "https://example.com/cluster1/article1" in urls
```

- [ ] **Step 2 : Vérifier que ces tests échouent**

```bash
cd backend
uv run pytest tests/test_agent_tools.py::TestSearchNewsTool::test_search_news_populates_loaded_articles tests/test_agent_tools.py::TestGetTopNewsTool::test_get_top_news_populates_loaded_articles -v
```

Résultat attendu : FAILED (AttributeError ou AssertionError — `ctx.context.loaded_articles` est vide).

- [ ] **Step 3 : Refactorer `tools.py`**

Remplacer le contenu de `backend/src/core/agent/tools.py` par :

```python
"""Function tools exposés à l'agent de chat NewsFoundry."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool

from core.agent.context import ChatRunContext
from core.config import TOP_NEWS_CLUSTERS
from core.news.search import search_news as _search_news
from core.worldnewsapi.worldnews import get_news_api


@function_tool
async def get_top_news(
    ctx: RunContextWrapper[ChatRunContext],
    source_country: str = "fr",
    language: str = "fr",
    date: str | None = None,
) -> str:
    """Get the top news headlines clustered from multiple sources for a country.

    Use this tool when the user asks for general daily news, top headlines,
    or 'what's happening today/this week' type of questions — with NO specific topic.
    Also use it when the user asks for news of a SPECIFIC PAST DATE.
    Do NOT use this for specific topic searches — use `search_news` instead.

    Args:
        source_country: ISO 3166-1 alpha-2 country code (default: "fr").
        language: ISO 639-1 language code (default: "fr").
        date: Date in YYYY-MM-DD format. Defaults to today if not provided.
              Use this when the user explicitly asks about a specific date.

    Returns:
        A Markdown-formatted list of top news clusters with titles and sources.
    """
    from core.news.reducer import reduce_clusters

    api = get_news_api()
    effective_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    response = await asyncio.to_thread(
        api.top_news,
        source_country=source_country,
        language=language,
        var_date=effective_date,
        _request_timeout=(5, 25),
    )

    clusters = reduce_clusters(response, top_n=TOP_NEWS_CLUSTERS)

    if not clusters:
        return f"Aucune actualité trouvée pour le {effective_date}."

    lines: list[str] = [f"## Top actualités — {effective_date}\n"]
    for i, cluster in enumerate(clusters, 1):
        title = cluster.titles[0] if cluster.titles else "Sans titre"
        summary = cluster.summaries[0] if cluster.summaries else ""
        summary_str = f"\n> {summary}" if summary else ""

        ctx.context.loaded_articles.append({
            "title": title,
            "summary": summary,
            "url": cluster.top_url,
        })

        lines.append(
            f"**{i}. {title}** ({cluster.article_count} articles){summary_str}\n"
            f"Source : {cluster.top_url}\n"
        )

    return "\n---\n".join(lines)


@function_tool
async def search_news(
    ctx: RunContextWrapper[ChatRunContext],
    query: str,
    language: str = "fr",
    max_results: int = 10,
) -> str:
    """Search for recent news articles on a specific topic.

    Use this tool when the user wants to explore a specific subject in depth
    (e.g. "tell me more about the Iran conflict", "what's happening with AI in France").
    Do NOT use this for general 'what's the news today' requests — use `get_top_news` instead.

    Args:
        query: Keywords or topic to search for (e.g. "conflit Iran", "IA France").
               Use the same language as the `language` parameter.
        language: ISO 639-1 language code for the articles (default: "fr").
        max_results: Number of articles to return, between 1 and 20 (default: 10).

    Returns:
        A Markdown-formatted list of articles with title, summary, date, and URL.
        Returns a message indicating no results if nothing was found.
    """
    articles = await _search_news(
        query=query, language=language, max_results=max_results
    )

    if not articles:
        return f"Aucun article trouvé pour la recherche : « {query} »."

    lines: list[str] = [f"## Résultats de recherche pour « {query} »\n"]
    for i, article in enumerate(articles, 1):
        date_str = f" — {article.publish_date}" if article.publish_date else ""
        summary_str = f"\n> {article.summary}" if article.summary else ""

        ctx.context.loaded_articles.append({
            "title": article.title,
            "summary": article.summary,
            "url": article.url,
        })

        lines.append(
            f"**{i}. {article.title}**{date_str}{summary_str}\nSource : {article.url}\n"
        )

    return "\n---\n".join(lines)
```

- [ ] **Step 4 : Typer l'agent dans `search_agent.py`**

Dans `backend/src/core/agent/search_agent.py`, modifier :

```python
from core.agent.context import ChatRunContext
from core.agent.tools import get_top_news, search_news

# ...

chat_agent = Agent[ChatRunContext](
    name="newsfoundry_chat_agent",
    instructions=_build_instructions,
    tools=[get_top_news, search_news],
    model=OpenAIChatCompletionsModel(
        model=LLM_MODEL,
        openai_client=_openai_client,
    ),
    model_settings=ModelSettings(
        temperature=0.4,
        max_tokens=AGENT_MAX_TOKENS,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    ),
)
```

- [ ] **Step 5 : Vérifier que les nouveaux tests passent**

```bash
cd backend
uv run pytest tests/test_agent_tools.py -v
```

Résultat attendu : tous les tests passent, y compris les deux nouveaux.

- [ ] **Step 6 : Commit**

```bash
git add backend/src/core/agent/tools.py backend/src/core/agent/search_agent.py backend/tests/test_agent_tools.py
git commit -m "feat: collect articles in ChatRunContext during tool calls"
```

---

## Task 5 : Intégration `ChatRunContext` dans `_process_message`

**Files:**
- Modify: `backend/src/api/chat_endpoints.py`

- [ ] **Step 1 : Mettre à jour les imports en haut de `chat_endpoints.py`**

Ajouter :

```python
from core.agent.context import ChatRunContext
from database.crud import (
    ...
    update_chat_loaded_articles_sync,
)
```

- [ ] **Step 2 : Modifier `_process_message` pour créer et passer le contexte**

Dans la fonction `_process_message`, remplacer le bloc Runner.run par :

```python
run_context = ChatRunContext(chat_id=chat_id)

try:
    result = await asyncio.wait_for(
        Runner.run(active_agent, input=openai_messages, context=run_context),
        timeout=LLM_TIMEOUT_SECONDS,
    )
    response_content = result.final_output
except asyncio.TimeoutError:
    logger.error(
        "[chat] LLM timeout after %.1fs — chat_id=%s base_url=%s model=%s",
        LLM_TIMEOUT_SECONDS,
        chat_id,
        LLM_BASE_URL,
        LLM_MODEL,
    )
    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="LLM request timed out"
    )
except Exception as exc:
    logger.error(
        "[chat] LLM provider error — chat_id=%s exc=%r base_url=%s model=%s",
        chat_id,
        exc,
        LLM_BASE_URL,
        LLM_MODEL,
    )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM provider error"
    )

# Fusionner les articles collectés avec les existants (dédupliqués par URL)
if run_context.loaded_articles:
    existing: list[dict] = chat.loaded_articles or []
    existing_urls = {a["url"] for a in existing}
    merged = existing + [
        a for a in run_context.loaded_articles if a["url"] not in existing_urls
    ]
    await asyncio.to_thread(update_chat_loaded_articles_sync, chat_id, merged)
```

- [ ] **Step 3 : Vérifier que les tests existants passent**

```bash
cd backend
uv run pytest tests/ -x -q
```

Résultat attendu : tous les tests passent.

- [ ] **Step 4 : Commit**

```bash
git add backend/src/api/chat_endpoints.py
git commit -m "feat: pass ChatRunContext to agent and persist loaded_articles after each run"
```

---

## Task 6 : Module RAG `core/rag/indexer.py`

**Files:**
- Create: `backend/src/core/rag/__init__.py`
- Create: `backend/src/core/rag/indexer.py`
- Create: `backend/tests/test_rag_indexer.py`

- [ ] **Step 1 : Écrire les tests qui vont échouer**

Créer `backend/tests/test_rag_indexer.py` :

```python
"""Tests unitaires pour core.rag.indexer.

Utilise MockEmbedding de LlamaIndex pour éviter de charger le modèle HuggingFace.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


@pytest.fixture(autouse=True)
def patch_embed(monkeypatch):
    """Remplace le singleton HuggingFace par MockEmbedding (384 dims)."""
    from llama_index.core.embeddings import MockEmbedding
    mock = MockEmbedding(embed_dim=384)
    monkeypatch.setattr("core.rag.indexer._embed", mock)


_ARTICLES = [
    {
        "title": "Conflit en Iran",
        "summary": "Les tensions s'intensifient au Moyen-Orient entre l'Iran et Israël.",
        "url": "https://example.com/iran",
    },
    {
        "title": "Élection présidentielle en France",
        "summary": "Les sondages donnent la gauche en tête à deux semaines du scrutin.",
        "url": "https://example.com/france",
    },
    {
        "title": "Intelligence artificielle : OpenAI sort GPT-5",
        "summary": "OpenAI a présenté son dernier modèle lors d'une conférence à San Francisco.",
        "url": "https://example.com/ia",
    },
]


def test_returns_list_of_dicts():
    from core.rag.indexer import build_index_and_retrieve
    results = build_index_and_retrieve(_ARTICLES, "Iran Moyen-Orient", top_k=2)
    assert isinstance(results, list)
    for item in results:
        assert "title" in item
        assert "summary" in item
        assert "url" in item


def test_returns_at_most_top_k_items():
    from core.rag.indexer import build_index_and_retrieve
    results = build_index_and_retrieve(_ARTICLES, "actualités", top_k=2)
    assert len(results) <= 2


def test_top_k_greater_than_articles_does_not_crash():
    from core.rag.indexer import build_index_and_retrieve
    results = build_index_and_retrieve(_ARTICLES, "actualités", top_k=100)
    assert len(results) <= len(_ARTICLES)


def test_empty_articles_returns_empty_list():
    from core.rag.indexer import build_index_and_retrieve
    results = build_index_and_retrieve([], "Iran", top_k=5)
    assert results == []


def test_caps_at_max_articles(monkeypatch):
    from core.rag import indexer
    monkeypatch.setattr(indexer, "_MAX_ARTICLES", 2)
    many = _ARTICLES * 5  # 15 articles
    from core.rag.indexer import build_index_and_retrieve
    results = build_index_and_retrieve(many, "actualités", top_k=10)
    assert len(results) <= 2


def test_all_returned_urls_come_from_input():
    from core.rag.indexer import build_index_and_retrieve
    input_urls = {a["url"] for a in _ARTICLES}
    results = build_index_and_retrieve(_ARTICLES, "France politique", top_k=3)
    for item in results:
        assert item["url"] in input_urls
```

- [ ] **Step 2 : Vérifier que ces tests échouent**

```bash
cd backend
uv run pytest tests/test_rag_indexer.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'core.rag'`

- [ ] **Step 3 : Créer le module RAG**

```bash
touch backend/src/core/rag/__init__.py
```

Créer `backend/src/core/rag/indexer.py` :

```python
"""Module RAG — construction d'un index vectoriel en mémoire via LlamaIndex.

Singleton `_embed` chargé une seule fois au démarrage du worker FastAPI
pour éviter de recharger PyTorch à chaque appel de l'endpoint /review.
"""

from __future__ import annotations

from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

_EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
_MAX_ARTICLES = 30

_embed = HuggingFaceEmbedding(model_name=_EMBED_MODEL)


def build_index_and_retrieve(
    articles: list[dict],
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Construit un index en mémoire et retourne les top-k articles pertinents.

    Args:
        articles: Liste de dicts {title, summary, url}.
        query: Requête textuelle pour le retrieval sémantique.
        top_k: Nombre maximum d'articles à retourner.

    Returns:
        Liste de dicts {title, summary, url} triée par pertinence décroissante.
        Retourne [] si articles est vide.
    """
    if not articles:
        return []

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

- [ ] **Step 4 : Vérifier que les tests passent**

```bash
cd backend
uv run pytest tests/test_rag_indexer.py -v
```

Résultat attendu : tous les tests passent.

- [ ] **Step 5 : Vérifier que l'ensemble des tests passent**

```bash
cd backend
uv run pytest tests/ -x -q
```

Résultat attendu : aucune régression.

- [ ] **Step 6 : Commit**

```bash
git add backend/src/core/rag/ backend/tests/test_rag_indexer.py
git commit -m "feat: add RAG indexer module with LlamaIndex VectorStoreIndex"
```

---

## Task 7 : Enrichissement de la revue avec le RAG

**Files:**
- Modify: `backend/src/api/chat_endpoints.py`

- [ ] **Step 1 : Ajouter l'import du module RAG**

En haut de `backend/src/api/chat_endpoints.py` ajouter :

```python
from core.rag.indexer import build_index_and_retrieve
```

- [ ] **Step 2 : Modifier `generate_chat_review` pour injecter les articles RAG**

Dans le handler `generate_chat_review` de `chat_endpoints.py`, après la construction de `llm_messages` et avant l'appel à `Runner.run(press_review_agent, ...)`, ajouter :

```python
# RAG : enrichir le contexte avec les articles sémantiquement pertinents
articles: list[dict] = chat.loaded_articles or []
if articles:
    user_msgs = [m["content"] for m in llm_messages if m["role"] == "user"]
    query = " ".join(user_msgs[-3:])
    relevant = build_index_and_retrieve(articles, query, top_k=5)
    if relevant:
        rag_block = "\n\n".join(
            f"**{a['title']}** ({a['url']})\n{a['summary']}" for a in relevant
        )
        llm_messages = [
            {
                "role": "system",
                "content": f"Articles pertinents identifiés pour cette revue :\n\n{rag_block}",
            },
            *llm_messages,
        ]
```

- [ ] **Step 3 : Vérifier que tous les tests passent**

```bash
cd backend
uv run pytest tests/ -x -q
```

Résultat attendu : aucune régression.

- [ ] **Step 4 : Commit**

```bash
git add backend/src/api/chat_endpoints.py
git commit -m "feat: enrich press review generation with RAG-retrieved articles"
```

---

## Task 8 : Dockerfile — pré-téléchargement du modèle

**Files:**
- Modify: `backend/Dockerfile`

- [ ] **Step 1 : Ajouter `HF_HOME` et le pré-téléchargement dans le stage builder**

Dans `backend/Dockerfile`, modifier le stage `builder` pour pré-télécharger le modèle :

```dockerfile
# ── Stage 1: install dependencies ──────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Pré-télécharger le modèle HuggingFace dans le cache de l'image
# Évite un téléchargement de 120 Mo à chaque démarrage du container Railway
ENV HF_HOME=/app/.hf_cache
RUN .venv/bin/python -c "\
from llama_index.embeddings.huggingface import HuggingFaceEmbedding; \
HuggingFaceEmbedding(model_name='paraphrase-multilingual-MiniLM-L12-v2')"
```

Et dans le stage runtime, copier le cache et définir `HF_HOME` :

```dockerfile
# ── Stage 2: minimal runtime image ─────────────────────────────────────────
FROM python:3.13-slim-bookworm

WORKDIR /app

RUN adduser --disabled-password --no-create-home --uid 1001 appuser

COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --from=builder --chown=appuser:appuser /app/.hf_cache ./.hf_cache

COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser src/ ./src/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/.hf_cache

COPY --chown=appuser:appuser docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys\ntry:\n urllib.request.urlopen('http://localhost:8000/')\nexcept Exception:\n sys.exit(1)"]

CMD ["./docker-entrypoint.sh"]
```

- [ ] **Step 2 : Vérifier le build Docker (si Docker est disponible)**

```bash
cd backend
docker build -t newsfoundry-backend-test . 2>&1 | tail -20
```

Résultat attendu : build réussi, modèle téléchargé dans le cache pendant le build.

- [ ] **Step 3 : Commit**

```bash
git add backend/Dockerfile
git commit -m "chore: pre-download HuggingFace embedding model in Docker build stage"
```

---

## Auto-révision du plan

**Couverture spec :**
- ✅ Section 1 — `Chat.loaded_articles` → Task 2
- ✅ Section 2 — `ChatRunContext` + tools refactoring → Tasks 3 + 4
- ✅ Section 2 — Intégration `_process_message` → Task 5
- ✅ Section 3 — Module RAG `indexer.py` → Task 6
- ✅ Section 3 — Enrichissement `/review` → Task 7
- ✅ Section 3 — Dépendances → Task 1
- ✅ Déploiement Railway / Dockerfile → Task 8
- ✅ Tests unitaires indexer → Task 6
- ✅ Tests unitaires tools → Task 4

**Cas limites testés :**
- `top_k > len(articles)` → Task 6, `test_top_k_greater_than_articles_does_not_crash`
- `articles = []` → Task 6, `test_empty_articles_returns_empty_list`
- Cap `_MAX_ARTICLES` → Task 6, `test_caps_at_max_articles`

**Cohérence des types :**
- `ChatRunContext.loaded_articles: list[dict]` utilisé dans Task 4 (tools), Task 5 (endpoint), Task 7 (review) ✅
- `update_chat_loaded_articles_sync(chat_id, articles: list)` créé Task 3, utilisé Task 5 ✅
- `build_index_and_retrieve(articles: list[dict], query: str, top_k: int) -> list[dict]` créé Task 6, utilisé Task 7 ✅
- `chat.loaded_articles` est `list` (JSON column SQLAlchemy) — pas de `json.loads()` dans Task 5 ni Task 7 ✅
