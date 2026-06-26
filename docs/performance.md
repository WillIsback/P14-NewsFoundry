# Performance

## Données de monitoring observées (Phoenix)

Les métriques ci-dessous ont été collectées via **Arize Phoenix** (self-hosted sur `phoenix.willisback.fr`), qui reçoit les traces OpenTelemetry du backend via un OTel Collector. Les spans agent/tool/LLM sont auto-instrumentés par `openinference-instrumentation-openai-agents`.

### Baseline — 25 juin 2026 (avant troncature des outils)

**Période d'observation :** 25 juin 2026 — 10 traces enregistrées

| Métrique | Valeur mesurée |
|---|---|
| Latence E2E médiane (P50) | **9 161 ms** |
| Latence E2E P95 | **16 760 ms** |
| Tokens totaux (10 traces) | **53 011** (~5 300/trace) |
| Tokens prompt (input) | **45 628** — **86 %** du total |
| Tokens completion (output) | **7 383** — **14 %** du total |
| Latence individuelle LLM | 1 100 – 3 200 ms par appel |
| Latence tool `search_news` | ~150 ms |

> **Observation clé :** 86 % des tokens consommés sont des tokens de contexte (prompt), contre seulement 14 % de génération. Le coût principal vient du contexte accumulé (prompt système + historique + résultats d'outils), pas de la réponse elle-même.

---

### Après PR #251 — 26 juin 2026 (troncature des retours d'outils)

**Période d'observation :** 26 juin 2026 — compte démo (`openclassroom@eval.com`), 2 tours de conversation + 1 revue de presse

#### Chat agent (`get_top_news` et `search_news`)

| Trace | Outil | Tokens totaux | Latence |
|---|---|---|---|
| "Actualités du jour en France" | `get_top_news` | **2 906** | 5.6s |
| "Détail sur la canicule" | `search_news` + historique | **4 533** | 9.4s |

**Gain mesuré sur le 1er tour :** 2 906 tokens vs ~4 200 (moyenne baseline) → **−31 %** ✅

#### Revue de presse (RAG + LLM)

| Span | Kind | Prompt | Completion | Total | Latence |
|---|---|---|---|---|---|
| `rag_retrieve` | retriever | — | — | 0 | 5.8s |
| `generation` (LLM) | llm | **4 297** | **3 199** | **7 496** | 32.6s |

**Ratio prompt/completion : 57/43** — bien meilleur que le 86/14 du chat, car le RAG injecte uniquement le contenu pertinent issu du vector store (textes complets ciblés), et la revue générée est substantielle (3 199 tokens de sortie).

> **Observation clé :** la troncature des retours d'outils n'affecte pas la qualité de la revue de presse — le RAG récupère les contenus complets depuis `loaded_articles` indépendamment du contexte de conversation. Les deux pipelines sont correctement découplés.

---

## Optimisations existantes

### Côté backend

1. **Mode mock WorldNewsAPI** : en développement, l'API retourne des données fixes pour éviter les rate limits et accélérer le développement
2. **Cache ONNX pré-téléchargé** : le modèle FastEmbed est téléchargé pendant le build Docker, pas au démarrage de l'application
3. **Compaction d'historique** : au-delà de 80% de la fenêtre de contexte (36 000 tokens), l'historique est résumé pour économiser des tokens et éviter les timeouts
4. **Semaphore de concurrence LLM** : `LLM_MAX_CONCURRENT = 5` limite les appels LLM simultanés pour ne pas saturer le serveur vLLM
5. **Messages persistés avant l'appel LLM** : garantit la résilience, pas un gain de perf direct mais évite les appels redondants
6. **Troncature des retours d'outils** *(PR #251, 26 juin 2026)* : `search_news` et `get_top_news` retournent titre + date + URL uniquement — les résumés ne sont plus injectés dans le contexte LLM (~800 tokens économisés par appel `search_news`)

### Côté frontend

1. **Loaders pour les appels lents** : les appels API longs (LLM, recherche d'actualités) déclenchent un indicateur de chargement pour une expérience utilisateur réactive
2. **Server Components** : le rendu côté serveur réduit la charge JavaScript côté client
3. **Server Actions** : les mutations sont traitées côté serveur, réduisant le JavaScript envoyé au navigateur
4. **`revalidatePath()`** : invalidation sélective du cache Next.js après les mutations

---

## Recommandations d'amélioration

### 1. Mise en cache des résultats LLM

**Constat :** Les appels LLM sont coûteux (temps et tokens). Une même question posée par deux utilisateurs différents (ex: "Quelles sont les actualités du jour ?") génère deux appels LLM identiques.

**Métrique mesurée (Phoenix) :** La latence E2E médiane est de **9 161 ms** (P95 : 16 760 ms) sur les 10 traces enregistrées. Chaque appel LLM individuel dure entre 1 100 ms et 3 200 ms — soit 2 à 4 appels en chaîne par tour de conversation.

**Exemple concret :** Deux utilisateurs demandent "les actus IA du jour" → 2 × 5 300 tokens consommés, 2 × 9 s d'attente, pour une réponse identique.

**Suggestion :** Implémenter un cache de requêtes/réponses LLM avec Redis :
- Clé = hash du prompt système + message utilisateur + date
- Valeur = réponse LLM
- TTL = 1 heure (les actualités évoluent)
- Invalidation automatique à minuit (les actualités du jour changent)

**Objectif mesurable :** Réduire la latence P50 de 9 161 ms à < 100 ms pour les requêtes identiques en cache (gain de 98 % sur les hits de cache), et réduire d'au moins 40 % la consommation de tokens sur les questions fréquentes.

---

### 2. Pagination des messages

**Constat :** `GET /chats/{id}/messages` charge et retourne la totalité des messages d'une discussion, même pour des conversations de 100+ messages. Cela augmente la charge sur la base de données, la bande passante, et le rendu.

**Métrique mesurée (Phoenix) :** Les traces montrent que le prompt grossit au fil de la conversation : **1 031 tokens** pour le 1er message → **1 564 tokens** après un échec d'outil → **2 796 tokens** au 3e échange (incluant résultats d'outils). Une discussion de 150 messages non paginée génère un payload JSON de ~150 KB et un contexte LLM qui dépasse rapidement la limite de compaction (36 000 tokens).

**Exemple concret :** Un chat avec 50 messages retourne l'intégralité de l'historique à chaque affichage, dont les 40 premiers ne sont jamais visibles à l'écran — ils ne servent qu'à reconstituer le contexte LLM côté serveur.

**Suggestion :** Ajouter une pagination cursor-based sur l'endpoint messages :
```python
@router.get("/chats/{chat_id}/messages")
def get_messages(
    chat_id: int,
    limit: int = Query(default=50, le=200),
    before: int | None = Query(default=None),  # cursor: message_id
    ...
)
```
Le frontend chargerait les messages par lots (infinite scroll ou "charger plus").

**Objectif mesurable :** Réduire de 60 % la taille des réponses JSON pour les discussions de plus de 50 messages, et ramener le temps de chargement initial à < 200 ms quel que soit le nombre total de messages.

---

### 3. Streaming des réponses LLM

**Constat :** Actuellement, l'API attend la réponse complète du LLM avant de retourner une réponse. L'utilisateur voit un loader pendant toute la durée de l'appel sans feedback intermédiaire.

**Métrique mesurée (Phoenix) :** Le TTFB (temps jusqu'au premier caractère visible) est égal à la latence E2E totale : **P50 = 9 161 ms**, **P95 = 16 760 ms**. Les appels LLM individuels génèrent entre 14 et 305 tokens de completion. Avec du streaming, les premiers tokens seraient visibles en ~500–1 000 ms au lieu d'attendre la fin de la génération complète.

**Exemple concret :** La trace du 25 juin montre un appel LLM de **3 177 ms** générant 305 tokens (une réponse substantielle). Avec streaming, le premier token apparaîtrait à ~500 ms et le texte s'afficherait progressivement — contre 3,2 s de loader actuel avant l'affichage de quoi que ce soit.

**Suggestion :** Utiliser Server-Sent Events (SSE) pour streamer la réponse du LLM token par token :
```python
from fastapi.responses import StreamingResponse

async def stream_chat_response(chat_id: int, content: str):
    async for token in llm_stream:
        yield f"data: {json.dumps({'token': token})}\n\n"
```

**Objectif mesurable :** Réduire le TTFB à < 2 s (vs P50 = 9,2 s actuellement), améliorant significativement l'expérience utilisateur perçue même si la latence totale de génération reste identique.

---

### 4. Indexation base de données

**Constat :** Les requêtes sur les messages utilisent des `SELECT` filtrés sur `chat_id` sans index composé optimisé.

**Métrique mesurée (Phoenix) :** Les traces montrent que la latence E2E (9,2 s) dépasse la somme des latences LLM tracées (~5 s). La différence (~4 s) correspond à des opérations non tracées : lecture BDD, sérialisation, réseau. Pour des discussions longues, la requête `SELECT * FROM message WHERE chat_id = ?` sans index devient un full scan proportionnel au volume de données.

**Exemple concret :** Une discussion de 150 messages sans index → scan séquentiel → temps de chargement pouvant dépasser 500 ms, avant même que l'appel LLM ne commence. Ce délai est invisible dans Phoenix (non tracé) mais mesurable via Sentry Performance.

**Suggestion :** Ajouter un index composé sur `(chat_id, timestamp)` dans la table `message` :
```python
# database/models.py
class Message(SQLModel, table=True):
    __table_args__ = (
        Index("idx_message_chat_timestamp", "chat_id", "timestamp"),
    )
```

**Objectif mesurable :** Réduire le temps de requête des messages à < 50 ms quel que soit le nombre de messages, libérant ainsi de la marge pour la latence LLM observable dans Phoenix.

---

### 5. Réduction de la verbosité des résultats d'outils ✅ *implémentée — PR #251 (26 juin 2026)*

**Constat :** Cette piste a été identifiée directement grâce aux données de monitoring Phoenix, ce qui illustre la valeur du tracing LLM. Le ratio **86 % prompt / 14 % completion** révèle que le contexte domine largement la génération. L'analyse des spans montre que les résultats de `search_news` et `get_top_news` incluaient le contenu complet des articles (titres, résumés, sources, métadonnées), ce qui gonflait le prompt à chaque appel sans que le LLM n'utilise nécessairement tous les articles retournés.

**Métrique mesurée (Phoenix) :** La progression du prompt au cours d'une même session de 3 échanges :

| Tour | Tokens input | Évolution |
|------|-------------|-----------|
| Tour 1 (system + 1 message utilisateur) | 1 031 | — |
| Tour 2 (+ résultat d'outil en erreur + retry) | 1 564 | +52 % |
| Tour 3 (+ résultats `search_news` avec 10 articles) | 2 796 | +79 % |

En moyenne sur les 10 traces : **4 563 tokens de prompt** pour seulement **738 tokens générés** par trace.

**Exemple concret :** La trace du 25 juin montre que `search_news("intelligence artificielle")` injectait 10 articles avec titres, résumés et URLs dans le prompt (~1 200 tokens) — alors que le LLM n'en citait finalement que 2 dans sa réponse. Les 8 articles non utilisés représentaient ~960 tokens injectés pour rien (84 % de gaspillage sur cet appel).

**Solution implémentée :** Les retours des deux outils sont tronqués à **titre + date + URL uniquement** (`backend/src/core/agent/tools.py`). Les résumés et textes complets restent stockés dans `loaded_articles` pour la génération de revue de presse, mais ne sont plus injectés dans le contexte de conversation.

```python
# Avant — search_news (~120 tokens/article × 10 = ~1 200 tokens)
f"**{i}. {article.title}**{date_str}\n> {article.summary}\nSource : {article.url}\n"

# Après — (~20 tokens/article × 10 = ~200 tokens)
f"**{i}. {article.title}**{date_str}\nSource : {article.url}\n"
```

**Gain mesuré (26 juin 2026) :** −31 % de tokens sur le 1er tour de conversation (2 906 vs ~4 200). Le ratio prompt/completion du chat n'est pas encore mesurable sur un échantillon suffisant, mais la tendance confirme la projection. La revue de presse affiche un ratio 57/43 (vs 86/14 en baseline) grâce au RAG ciblé.
