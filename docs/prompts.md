# Ingénierie des prompts

Tous les prompts sont centralisés dans `backend/src/core/prompts.py`.

## Principes généraux

1. **Centralisation :** tous les prompts sont dans un seul fichier pour faciliter la maintenance et l'itération
2. **Identité commune :** chaque prompt commence par `_IDENTITY` qui définit le rôle de base de l'assistant
3. **Langue :** les prompts conversationnels sont en français, les prompts de classification sont en anglais (compatibilité avec les modèles)
4. **Format structuré :** la sortie des revues de presse utilise Markdown pour une lisibilité maximale

## Contexte d'actualités

Lorsqu'un utilisateur démarre une discussion avec un contexte d'actualités (via la page d'accueil), un prompt système personnalisé est généré par `build_news_system_prompt()`. Ce prompt inclut :
- La liste des clusters d'actualités (catégorie, titre, nombre de sources, URL principale, résumé)
- La consigne de ne répondre qu'à partir des informations fournies

Ce prompt est **gelé** au premier message (`system_prompt` stocké sur le modèle `Chat`) pour garantir la continuité de la conversation lors des sessions ultérieures. Sans ce gel, un agent de chat pourrait perdre le fil contextuel d'une analyse d'actualités entamée la veille.

## Revues de presse

Le prompt `PRESS_REVIEW_PROMPT` est utilisé dans deux contextes :

1. **Revue directe** (`POST /reviews`) : l'utilisateur fournit des articles, le LLM produit une revue structurée avec `call_llm_structured`
2. **Revue depuis une discussion** (`POST /chats/{id}/review`) : l'historique de la conversation est transmis à l'agent spécialisé `press_review_agent`, enrichi par RAG

### Choix d'implémentation

- **Sortie structurée** (Pydantic `_PressReviewLLMOutput`) : garantit que le titre et le contenu sont bien formatés et séparés
- **Markdown** pour le contenu : permet un rendu riche dans le frontend (`react-markdown`) avec titres, listes, citations, et gras
- **Instruction de ne pas inventer** : essentielle pour une revue de presse factuelle

## Chat conversationnel

Le prompt `CHAT_PROMPT` est utilisé pour les conversations sans contexte d'actualités. Il est volontairement simple et direct.

## Compaction d'historique

`COMPACTION_PROMPT` est utilisé par `compact_history_if_needed()` dans `llm_provider.py`. La compaction est déclenchée lorsque l'historique atteint 80% de la fenêtre de contexte (36 000 tokens).

Les 6 messages les plus récents sont conservés textuellement. Le reste est résumé. Ce choix préserve les détails récents tout en contrôlant la taille du contexte.

## Classification des clusters

`CLUSTER_LABELING_PROMPT` est utilisé dans la pipeline d'ingestion d'actualités (`labeler.py`). Chaque cluster reçoit :
1. Un titre synthétique
2. Un résumé factuel (~80 mots, dans la langue des titres d'articles)
3. Une catégorie parmi : politics, sports, business, technology, entertainment, health, science, lifestyle, culture, environment, other

Le résultat est un objet JSON structuré, facile à parser et à stocker.

## Instructions d'agent

Les agents utilisent `generate_instructions()` (dans `search_agent.py`) et `_build_instructions()` (dans `press_review_agent.py`) qui injectent dynamiquement :
- La date courante (évite les refus "future date")
- Les règles d'utilisation des outils
- Les consignes de citation des sources

## Paramètres LLM

| Paramètre | Valeur | Raison |
|-----------|--------|--------|
| `AGENT_MAX_TOKENS` | 4096 | Suffisant pour une revue de presse structurée (10+ articles) |
| `LLM_TIMEOUT_SECONDS` | 60 | Tolérant envers les modèles sous contention GPU |
| `LLM_MAX_CONCURRENT` | 5 | Évite de saturer le serveur vLLM |
| `LLM_CONTEXT_WINDOW_TOKENS` | 36000 | Adapté à la fenêtre de contexte du modèle |
| `LLM_COMPACT_THRESHOLD_RATIO` | 0.80 | Déclenche la compaction avant d'atteindre la limite |
| `LLM_COMPACT_RECENT_KEEP` | 6 | Préserve le contexte récent de la conversation |

## Désactivation du tracing

Le tracing OpenAI Agents SDK est désactivé (`set_tracing_disabled(True)`) car il tenterait d'atteindre `api.openai.com` avec la clé API vLLM locale, générant un bruit inutile dans les logs.
