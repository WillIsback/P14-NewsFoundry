"""Module RAG — construction d'un index vectoriel en mémoire via LlamaIndex.

Singleton `_embed` chargé une seule fois au démarrage du worker FastAPI
pour éviter de recharger le modèle ONNX à chaque appel de l'endpoint /review.
"""

from __future__ import annotations

from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding

# fastembed lit FASTEMBED_CACHE_PATH automatiquement (défini dans le Dockerfile)
_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_MAX_ARTICLES = 30

_embed = FastEmbedEmbedding(model_name=_EMBED_MODEL)


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
