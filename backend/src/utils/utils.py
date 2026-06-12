"""Utilitaires transverses du backend NewsFoundry.

Ce module centralise les helpers réutilisables qui n'appartiennent pas à un
domaine métier précis :

- Sanitization des entrées utilisateur (prompt-injection, homoglyphes)
- Estimation du nombre de tokens (heuristique GPT)
- Modèle Pydantic ``LLMMessage`` (validation + sanitization automatique)
"""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, Field, field_validator

from core.config import LLM_MAX_INPUT_CHARS

# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

# Caractères de contrôle dangereux (vecteur prompt-injection) :
# tout ce qui est sous U+0020 sauf tab (\x09) et newline (\x0a).
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(text: str, max_chars: int = LLM_MAX_INPUT_CHARS) -> str:
    """Nettoie un texte avant de l'envoyer au LLM.

    Supprime les caractères de contrôle et normalise l'unicode (NFC) pour
    prévenir les attaques par homoglyphes. Lève ``ValueError`` si la
    longueur dépasse ``max_chars`` après nettoyage.

    Args:
        text: Texte brut fourni par l'utilisateur.
        max_chars: Limite de longueur en caractères (défaut : ``LLM_MAX_INPUT_CHARS``).

    Returns:
        Texte nettoyé et normalisé.

    Raises:
        ValueError: Si le texte dépasse ``max_chars`` caractères.
    """
    text = _CONTROL_CHAR_RE.sub("", text)
    text = unicodedata.normalize("NFC", text)
    if len(text) > max_chars:
        raise ValueError(
            f"Message content exceeds maximum length of {max_chars} characters"
        )
    return text


# ---------------------------------------------------------------------------
# Estimation de tokens
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    """Estime le nombre de tokens dans un texte (heuristique ~4 chars/token).

    Adapté aux modèles de la famille GPT. Retourne au minimum 1.
    """
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Modèle LLMMessage (validation + sanitization automatique)
# ---------------------------------------------------------------------------


class LLMMessage(BaseModel):
    """Un message de conversation unique destiné au LLM.

    Le contenu est automatiquement sanitisé par le validator :
    caractères de contrôle supprimés, unicode normalisé (NFC),
    longueur plafonnée à ``LLM_MAX_INPUT_CHARS``.
    """

    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return sanitize_text(v)
