# Performance

## Optimisations existantes

### Côté backend

1. **Mode mock WorldNewsAPI** : en développement, l'API retourne des données fixes pour éviter les rate limits et accélérer le développement
2. **Cache ONNX pré-téléchargé** : le modèle FastEmbed est téléchargé pendant le build Docker, pas au démarrage de l'application
3. **Compaction d'historique** : au-delà de 80% de la fenêtre de contexte (36 000 tokens), l'historique est résumé pour économiser des tokens et éviter les timeouts
4. **Semaphore de concurrence LLM** : `LLM_MAX_CONCURRENT = 5` limite les appels LLM simultanés pour ne pas saturer le serveur vLLM
5. **Messages persistés avant l'appel LLM** : garantit la résilience, pas un gain de perf direct mais évite les appels redondants

### Côté frontend

1. **Loaders pour les appels lents** : les appels API longs (LLM, recherche d'actualités) déclenchent un indicateur de chargement pour une expérience utilisateur réactive
2. **Server Components** : le rendu côté serveur réduit la charge JavaScript côté client
3. **Server Actions** : les mutations sont traitées côté serveur, réduisant le JavaScript envoyé au navigateur
4. **`revalidatePath()`** : invalidation sélective du cache Next.js après les mutations

## Recommandations d'amélioration

### 1. Mise en cache des résultats LLM

**Constat :** Les appels LLM sont coûteux (temps et tokens). Une même question posée par deux utilisateurs différents (ex: "Quelles sont les actualités du jour ?") génère deux appels LLM identiques.

**Métrique :** Le temps de réponse médian des endpoints `/chats/message` et `/chats/{id}/messages` est d'environ 5-15 secondes (attente LLM incluse).

**Suggestion :** Implémenter un cache de requêtes/réponses LLM avec Redis :
- Clé = hash du prompt système + message utilisateur + date
- Valeur = réponse LLM
- TTL = 1 heure (les actualités évoluent)
- Invalidation automatique à minuit (les actualités du jour changent)

**Objectif mesurable :** Réduire de 40% le temps de réponse moyen des endpoints de chat pour les questions fréquentes (ex: "résume les actualités politiques").

### 2. Pagination des messages

**Constat :** `GET /chats/{id}/messages` charge et retourne la totalité des messages d'une discussion, même pour des conversations de 100+ messages. Cela augmente la charge sur la base de données, la bande passante, et le rendu.

**Métrique :** Une discussion de 150 messages génère ~150 KB de données JSON + 150 appels au LLM pour la compaction.

**Suggestion :** Ajouter une pagination avec `limit` et `offset` (ou cursor-based) :
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

**Objectif mesurable :** Réduire de 60% la taille des réponses pour les discussions de plus de 50 messages (les discussions récentes étant les plus consultées).

### 3. Streaming des réponses LLM

**Constat :** Actuellement, l'API attend la réponse complète du LLM avant de retourner une réponse. L'utilisateur voit un loader pendant 5-15 secondes sans feedback intermédiaire.

**Métrique :** Le temps jusqu'au premier caractère visible est égal au temps total de réponse (5-15s).

**Suggestion :** Utiliser le Server-Sent Events (SSE) ou WebSockets pour streamer la réponse du LLM token par token :
1. Le frontend ouvre une connexion SSE
2. Le backend forwarde les tokens du LLM en temps réel
3. L'utilisateur voit le texte apparaître progressivement (type ChatGPT)

```python
from fastapi.responses import StreamingResponse

async def stream_chat_response(chat_id: int, content: str):
    # ...
    async for token in llm_stream:
        yield f"data: {json.dumps({'token': token})}\n\n"
```

**Objectif mesurable :** Réduire le temps jusqu'au premier caractère visible à < 2 secondes (vs 5-15s actuellement), améliorant significativement l'expérience utilisateur perçue.

### 4. Indexation base de données

**Constat :** Les requêtes sur les messages utilisent des `SELECT` sans index optimisé sur `chat_id`.

**Métrique :** Le temps de chargement des messages peut dépasser 500ms pour les discussions très longues.

**Suggestion :** Ajouter un index composé sur `(chat_id, timestamp)` dans la table `message` :
```python
# database/models.py
class Message(SQLModel, table=True):
    __table_args__ = (
        Index("idx_message_chat_timestamp", "chat_id", "timestamp"),
    )
```

**Objectif mesurable :** Réduire le temps de requête des messages à < 50ms, quel que soit le nombre de messages.
