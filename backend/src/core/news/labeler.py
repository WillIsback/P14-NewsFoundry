"""ClusterLabeler — appelle le LLM pour labelliser les clusters de news.

Envoie tous les clusters en un seul appel structuré et retourne
une liste de LabeledCluster ordonnée comme l'input.
"""

from typing import Literal

from pydantic import BaseModel

from core.llm_provider import LLMStructuredRequest, call_llm_structured
from utils.utils import LLMMessage
from core.news.reducer import ClusterInput
from core.prompts import CLUSTER_LABELING_PROMPT

VALID_CATEGORIES = Literal[
    "politics",
    "sports",
    "business",
    "technology",
    "entertainment",
    "health",
    "science",
    "lifestyle",
    "culture",
    "environment",
    "other",
]


class LabeledCluster(BaseModel):
    cluster_title: str
    cluster_summary: str
    category: VALID_CATEGORIES
    article_count: int
    top_url: str


class LabeledClusters(BaseModel):
    clusters: list[LabeledCluster]


_MAX_TITLES_PER_CLUSTER = 3
_MAX_TITLE_CHARS = 100


def _build_user_message(inputs: list[ClusterInput]) -> str:
    """Formate les clusters en message utilisateur pour le LLM.

    Limite à _MAX_TITLES_PER_CLUSTER titres par cluster et
    _MAX_TITLE_CHARS caractères par titre pour rester sous
    LLM_MAX_INPUT_CHARS.
    """
    lines: list[str] = []
    for inp in inputs:
        lines.append(
            f"Cluster {inp.cluster_index + 1} ({inp.article_count} articles) :"
        )
        for title in inp.titles[:_MAX_TITLES_PER_CLUSTER]:
            lines.append(f"- {title[:_MAX_TITLE_CHARS]}")
        lines.append("")
    return "\n".join(lines).strip()


async def label_clusters(
    inputs: list[ClusterInput],
    model: str | None = None,
) -> list[LabeledCluster]:
    """Envoie les clusters au LLM en un seul appel structuré pour labellisation.

    Args:
        inputs: Liste de ClusterInput issus de reduce_clusters.
        model: Nom du modèle LLM à utiliser (None = défaut du provider).

    Returns:
        Liste de LabeledCluster dans le même ordre que inputs.
    """
    if not inputs:
        return []

    user_content = _build_user_message(inputs)

    request_kwargs: dict = dict(
        system_prompt=CLUSTER_LABELING_PROMPT,
        messages=[LLMMessage(role="user", content=user_content)],
        max_tokens=4096,
        timeout=180.0,  # labeling 25 clusters needs more time than the default
    )
    if model is not None:
        request_kwargs["model"] = model

    request = LLMStructuredRequest(**request_kwargs)
    response = await call_llm_structured(request, LabeledClusters)
    return response.clusters
