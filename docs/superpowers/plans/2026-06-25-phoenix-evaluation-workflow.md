# Phoenix Evaluation Workflow — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Déployer un eval-worker Docker sur le VPS qui évalue les traces Phoenix (sélection outil, retrieval, génération) toutes les 30 min et annote les résultats dans Phoenix UI.

**Architecture:** Un conteneur Python éphémère (`eval-worker`) dans la stack monitoring du VPS se connecte à `http://phoenix:6006` via le réseau Docker interne, lit les spans des 60 dernières minutes, les évalue via règles (étapes 1-2) et LLM-as-judge arize-phoenix-evals (étape 3), puis poste les annotations via `px.Client().log_evaluations()`. Un cron système VPS (`*/30 * * * *`) déclenche le cycle.

**Tech Stack:** arize-phoenix, arize-phoenix-evals, pandas, openai (client vLLM), Docker Compose, Tailscale (VPS→GB10), pytest.

**Toutes les opérations se font en SSH sur le VPS** (`ssh ubuntu@51.255.206.255`) sauf les étapes Tailscale admin console.

---

## Structure des fichiers

```
~/infra/stacks/monitoring/
├── docker-compose.yml          ← MODIFIER : ajouter service eval-worker
├── .env                        ← CRÉER : EVAL_LLM_BASE_URL, EVAL_LLM_MODEL
└── eval/
    ├── Dockerfile              ← CRÉER
    ├── requirements.txt        ← CRÉER
    ├── config.py               ← CRÉER : env vars + constantes
    ├── eval_worker.py          ← CRÉER : orchestrateur principal
    ├── evaluators/
    │   ├── __init__.py         ← CRÉER (vide)
    │   ├── tool_evaluator.py   ← CRÉER : règles sélection outil
    │   ├── retrieval_evaluator.py ← CRÉER : règles qualité retrieval
    │   └── generation_evaluator.py ← CRÉER : LLM-judge hallucination + relevance
    └── tests/
        ├── __init__.py         ← CRÉER (vide)
        ├── test_tool_evaluator.py
        ├── test_retrieval_evaluator.py
        ├── test_generation_evaluator.py
        └── test_eval_worker.py
```

---

## Task 0 : Tailscale ACL — ajouter tag:vps et grants

**Contexte :** Le VPS doit pouvoir atteindre le vLLM sur le GB10 (`100.70.22.24:30000`) via Tailscale. Le GB10 reçoit le tag `tag:gpu`, le VPS reçoit `tag:vps`. Les grants limitent `tag:vps` au seul port 30000 du GB10 — aucun accès aux machines perso.

**Fichiers :** Tailscale admin console (navigateur), aucun fichier du repo.

- [ ] **Step 1 : Ajouter tag:gpu au GB10 dans la console Tailscale**

  Aller sur https://login.tailscale.com/admin/machines → chercher `spark-787d-1` → menu "Edit tags" → ajouter `tag:gpu` → sauvegarder.

- [ ] **Step 2 : Mettre à jour les ACL Tailscale**

  Aller sur https://login.tailscale.com/admin/acls → remplacer (ou fusionner) avec :

  ```json
  {
    "tagOwners": {
      "tag:railway": ["autogroup:admin"],
      "tag:vps":     ["autogroup:admin"],
      "tag:gpu":     ["autogroup:admin"]
    },
    "grants": [
      {
        "src": ["tag:railway"],
        "dst": ["tag:gpu"],
        "ip":  ["*"]
      },
      {
        "src": ["tag:vps"],
        "dst": ["tag:gpu"],
        "ip":  ["tcp:30000"]
      }
    ]
  }
  ```

  Sauvegarder. Vérifier dans "Access controls" que le diff est correct.

- [ ] **Step 3 : Vérifier que le GB10 apparaît avec tag:gpu**

  Dans la liste des machines Tailscale, `spark-787d-1` doit afficher `tag:gpu`.

---

## Task 1 : Installer Tailscale sur le VPS et rejoindre le tailnet

**Fichiers :** système VPS uniquement.

- [ ] **Step 1 : Installer Tailscale**

  ```bash
  ssh ubuntu@51.255.206.255
  curl -fsSL https://tailscale.com/install.sh | sh
  ```

  Attendu : `Installation complete!`

- [ ] **Step 2 : Générer une auth key Tailscale pour le VPS**

  Aller sur https://login.tailscale.com/admin/settings/keys → "Generate auth key" → cocher **Reusable** + **Tags** → tag : `tag:vps` → copier la clé (`tskey-auth-...`).

- [ ] **Step 3 : Rejoindre le tailnet avec tag:vps**

  ```bash
  sudo tailscale up --authkey=tskey-auth-XXXXX --advertise-tags=tag:vps
  ```

  Attendu : pas d'erreur, le nœud apparaît dans la console Tailscale avec tag `tag:vps`.

- [ ] **Step 4 : Vérifier la connectivité vers le GB10**

  ```bash
  curl -s http://100.70.22.24:30000/v1/models | python3 -m json.tool | head -20
  ```

  Attendu : JSON listant les modèles disponibles sur le vLLM.

---

## Task 2 : Bootstrap de la structure eval/ sur le VPS

**Fichiers :** `~/infra/stacks/monitoring/eval/` (créer arborescence).

- [ ] **Step 1 : Créer les dossiers**

  ```bash
  ssh ubuntu@51.255.206.255
  mkdir -p ~/infra/stacks/monitoring/eval/evaluators
  mkdir -p ~/infra/stacks/monitoring/eval/tests
  touch ~/infra/stacks/monitoring/eval/evaluators/__init__.py
  touch ~/infra/stacks/monitoring/eval/tests/__init__.py
  ```

- [ ] **Step 2 : Créer le fichier .env de la stack monitoring**

  ```bash
  cat > ~/infra/stacks/monitoring/.env << 'EOF'
  EVAL_LLM_BASE_URL=http://100.70.22.24:30000/v1
  EVAL_LLM_MODEL=Qwen/Qwen3-35B-A22B
  EOF
  ```

  Remplacer `Qwen/Qwen3-35B-A22B` par le nom exact du modèle retourné à l'étape Task 1 Step 4.

- [ ] **Step 3 : Commit du .env.example dans le repo infra (si versionné)**

  Sur le VPS, si `~/infra/` est un repo git :
  ```bash
  cd ~/infra
  cat > stacks/monitoring/.env.example << 'EOF'
  EVAL_LLM_BASE_URL=http://<tailscale-ip-gpu>:30000/v1
  EVAL_LLM_MODEL=<model-name>
  EOF
  git add stacks/monitoring/.env.example
  git commit -m "chore: add eval-worker env example"
  ```

---

## Task 3 : config.py

**Fichiers :**
- Créer : `~/infra/stacks/monitoring/eval/config.py`

- [ ] **Step 1 : Écrire config.py**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/config.py << 'EOF'
  import os

  PHOENIX_ENDPOINT = os.getenv("PHOENIX_ENDPOINT", "http://phoenix:6006")
  PHOENIX_PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "newsfoundry")
  EVAL_LLM_BASE_URL = os.environ["EVAL_LLM_BASE_URL"]
  EVAL_LLM_MODEL = os.environ["EVAL_LLM_MODEL"]
  EVAL_LOOKBACK_MINUTES = int(os.getenv("EVAL_LOOKBACK_MINUTES", "60"))

  # Mots-clés indiquant une query générique → get_top_news attendu
  GENERIC_QUERY_KEYWORDS = {
      "actualités", "news", "quoi de neuf", "tendances", "top",
      "trending", "aujourd'hui", "today", "latest", "récent",
  }
  EOF
  ```

---

## Task 4 : tool_evaluator.py (TDD)

**Fichiers :**
- Créer : `~/infra/stacks/monitoring/eval/evaluators/tool_evaluator.py`
- Créer : `~/infra/stacks/monitoring/eval/tests/test_tool_evaluator.py`

Les spans Phoenix sont des DataFrames pandas avec colonnes :
- `context.span_id` — identifiant du span
- `context.trace_id` — identifiant de la trace parente
- `attributes.openinference.span.kind` — `AGENT`, `TOOL`, `LLM`, `RETRIEVER`
- `attributes.input.value` — texte d'entrée (query utilisateur pour AGENT)
- `attributes.tool.name` — nom du tool (`get_top_news` / `search_news`) pour TOOL spans

- [ ] **Step 1 : Écrire les tests**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/tests/test_tool_evaluator.py << 'EOF'
  import pandas as pd
  import pytest
  from evaluators.tool_evaluator import evaluate_tool_used, evaluate_tool_relevance


  def make_agent_span(span_id: str, trace_id: str, query: str) -> dict:
      return {
          "context.span_id": span_id,
          "context.trace_id": trace_id,
          "attributes.input.value": query,
      }


  def make_tool_span(span_id: str, trace_id: str, tool_name: str) -> dict:
      return {
          "context.span_id": span_id,
          "context.trace_id": trace_id,
          "attributes.tool.name": tool_name,
      }


  class TestEvaluateToolUsed:
      def test_agent_with_tool_scores_1(self):
          agents = pd.DataFrame([make_agent_span("a1", "t1", "actualités")])
          tools = pd.DataFrame([make_tool_span("t1", "t1", "get_top_news")])
          result = evaluate_tool_used(agents, tools)
          assert result.loc["a1", "score"] == 1.0
          assert result.loc["a1", "label"] == "used"

      def test_agent_without_tool_scores_0(self):
          agents = pd.DataFrame([make_agent_span("a1", "t1", "bonjour")])
          tools = pd.DataFrame(columns=["context.span_id", "context.trace_id", "attributes.tool.name"])
          result = evaluate_tool_used(agents, tools)
          assert result.loc["a1", "score"] == 0.0
          assert result.loc["a1", "label"] == "missing"

      def test_multiple_traces_independent(self):
          agents = pd.DataFrame([
              make_agent_span("a1", "t1", "news"),
              make_agent_span("a2", "t2", "hello"),
          ])
          tools = pd.DataFrame([make_tool_span("s1", "t1", "get_top_news")])
          result = evaluate_tool_used(agents, tools)
          assert result.loc["a1", "score"] == 1.0
          assert result.loc["a2", "score"] == 0.0


  class TestEvaluateToolRelevance:
      def test_generic_query_get_top_news_is_relevant(self):
          agents = pd.DataFrame([make_agent_span("a1", "t1", "quoi de neuf aujourd'hui ?")])
          tools = pd.DataFrame([make_tool_span("s1", "t1", "get_top_news")])
          result = evaluate_tool_relevance(agents, tools)
          assert result.loc["s1", "score"] == 1.0
          assert result.loc["s1", "label"] == "relevant"

      def test_generic_query_search_news_is_wrong(self):
          agents = pd.DataFrame([make_agent_span("a1", "t1", "actualités du jour")])
          tools = pd.DataFrame([make_tool_span("s1", "t1", "search_news")])
          result = evaluate_tool_relevance(agents, tools)
          assert result.loc["s1", "score"] == 0.0
          assert result.loc["s1", "label"] == "wrong_tool"

      def test_specific_query_search_news_is_relevant(self):
          agents = pd.DataFrame([make_agent_span("a1", "t1", "tensions entre Israël et Iran")])
          tools = pd.DataFrame([make_tool_span("s1", "t1", "search_news")])
          result = evaluate_tool_relevance(agents, tools)
          assert result.loc["s1", "score"] == 1.0
          assert result.loc["s1", "label"] == "relevant"

      def test_specific_query_get_top_news_is_wrong(self):
          agents = pd.DataFrame([make_agent_span("a1", "t1", "Apple iPhone 17 rumeurs")])
          tools = pd.DataFrame([make_tool_span("s1", "t1", "get_top_news")])
          result = evaluate_tool_relevance(agents, tools)
          assert result.loc["s1", "score"] == 0.0
          assert result.loc["s1", "label"] == "wrong_tool"

      def test_no_tool_spans_returns_empty(self):
          agents = pd.DataFrame([make_agent_span("a1", "t1", "test")])
          tools = pd.DataFrame(columns=["context.span_id", "context.trace_id", "attributes.tool.name"])
          result = evaluate_tool_relevance(agents, tools)
          assert result.empty
  EOF
  ```

- [ ] **Step 2 : Vérifier que les tests échouent (module inexistant)**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  python3 -m pytest tests/test_tool_evaluator.py -v 2>&1 | head -20
  ```

  Attendu : `ModuleNotFoundError: No module named 'evaluators'`

- [ ] **Step 3 : Implémenter tool_evaluator.py**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/evaluators/tool_evaluator.py << 'EOF'
  """Évaluateurs règles pour la sélection d'outil (étape 1)."""

  import pandas as pd
  from config import GENERIC_QUERY_KEYWORDS


  def evaluate_tool_used(
      agent_spans: pd.DataFrame,
      tool_spans: pd.DataFrame,
  ) -> pd.DataFrame:
      """Score 1.0/used si l'agent a appelé ≥1 outil, 0.0/missing sinon.

      Index de retour : context.span_id des spans AGENT.
      Colonnes : score (float), label (str).
      """
      records = []
      for _, agent in agent_spans.iterrows():
          span_id = agent["context.span_id"]
          trace_id = agent["context.trace_id"]
          used = not tool_spans[tool_spans["context.trace_id"] == trace_id].empty
          records.append({
              "span_id": span_id,
              "score": 1.0 if used else 0.0,
              "label": "used" if used else "missing",
          })
      df = pd.DataFrame(records)
      return df.set_index("span_id") if not df.empty else pd.DataFrame(
          columns=["score", "label"]
      )


  def _is_generic_query(query: str) -> bool:
      tokens = set(query.lower().split())
      return bool(tokens & GENERIC_QUERY_KEYWORDS) or len(tokens) <= 2


  def evaluate_tool_relevance(
      agent_spans: pd.DataFrame,
      tool_spans: pd.DataFrame,
  ) -> pd.DataFrame:
      """Score 1.0/relevant si le bon outil a été choisi, 0.0/wrong_tool sinon.

      Index de retour : context.span_id des spans TOOL.
      Colonnes : score (float), label (str).
      """
      if tool_spans.empty:
          return pd.DataFrame(columns=["score", "label"])

      records = []
      for _, tool in tool_spans.iterrows():
          span_id = tool["context.span_id"]
          trace_id = tool["context.trace_id"]
          tool_name = tool.get("attributes.tool.name", "")

          parent = agent_spans[agent_spans["context.trace_id"] == trace_id]
          if parent.empty:
              continue

          query = str(parent.iloc[0].get("attributes.input.value", ""))
          generic = _is_generic_query(query)
          correct = (generic and tool_name == "get_top_news") or (
              not generic and tool_name == "search_news"
          )
          records.append({
              "span_id": span_id,
              "score": 1.0 if correct else 0.0,
              "label": "relevant" if correct else "wrong_tool",
          })

      df = pd.DataFrame(records)
      return df.set_index("span_id") if not df.empty else pd.DataFrame(
          columns=["score", "label"]
      )
  EOF
  ```

- [ ] **Step 4 : Lancer les tests (avec PYTHONPATH)**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/test_tool_evaluator.py -v
  ```

  Attendu : `8 passed`

---

## Task 5 : retrieval_evaluator.py (TDD)

**Fichiers :**
- Créer : `~/infra/stacks/monitoring/eval/evaluators/retrieval_evaluator.py`
- Créer : `~/infra/stacks/monitoring/eval/tests/test_retrieval_evaluator.py`

Les spans RETRIEVER ont :
- `attributes.rag.top_k` — nombre de documents demandés
- `attributes.rag.retrieved_count` — nombre de documents effectivement retournés
- `attributes.input.value` — query de recherche
- `attributes.retrieval.documents.0.document.metadata.title`, `.1.`, `.2.`, … — titres des articles

- [ ] **Step 1 : Écrire les tests**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/tests/test_retrieval_evaluator.py << 'EOF'
  import pandas as pd
  import pytest
  from evaluators.retrieval_evaluator import (
      evaluate_retrieval_coverage,
      evaluate_retrieval_overlap,
      _jaccard,
  )


  def make_retriever_span(
      span_id: str,
      top_k: int,
      retrieved: int,
      query: str,
      titles: list[str],
  ) -> dict:
      row = {
          "context.span_id": span_id,
          "attributes.rag.top_k": top_k,
          "attributes.rag.retrieved_count": retrieved,
          "attributes.input.value": query,
      }
      for i, title in enumerate(titles):
          row[f"attributes.retrieval.documents.{i}.document.metadata.title"] = title
      return row


  class TestEvaluateCoverage:
      def test_full_coverage(self):
          spans = pd.DataFrame([make_retriever_span("r1", 5, 5, "test", ["t"] * 5)])
          result = evaluate_retrieval_coverage(spans)
          assert result.loc["r1", "score"] == 1.0

      def test_partial_coverage(self):
          spans = pd.DataFrame([make_retriever_span("r1", 5, 3, "test", ["t"] * 3)])
          result = evaluate_retrieval_coverage(spans)
          assert abs(result.loc["r1", "score"] - 0.6) < 0.001

      def test_zero_top_k_scores_zero(self):
          spans = pd.DataFrame([make_retriever_span("r1", 0, 0, "test", [])])
          result = evaluate_retrieval_coverage(spans)
          assert result.loc["r1", "score"] == 0.0


  class TestJaccard:
      def test_identical_texts(self):
          assert _jaccard("apple iphone", "apple iphone") == 1.0

      def test_no_overlap(self):
          assert _jaccard("apple iphone", "ukraine guerre") == 0.0

      def test_partial_overlap(self):
          score = _jaccard("apple iphone rumeurs", "apple nouvelles")
          assert 0.0 < score < 1.0

      def test_empty_string(self):
          assert _jaccard("", "test") == 0.0


  class TestEvaluateOverlap:
      def test_high_overlap(self):
          spans = pd.DataFrame([make_retriever_span(
              "r1", 2, 2, "apple iphone", ["Apple annonce iPhone 17", "Apple événement"]
          )])
          result = evaluate_retrieval_overlap(spans)
          assert result.loc["r1", "score"] > 0.3

      def test_no_overlap(self):
          spans = pd.DataFrame([make_retriever_span(
              "r1", 2, 2, "ukraine conflit", ["Apple iPhone", "Tesla Model 3"]
          )])
          result = evaluate_retrieval_overlap(spans)
          assert result.loc["r1", "score"] == 0.0

      def test_no_titles_scores_zero(self):
          spans = pd.DataFrame([make_retriever_span("r1", 3, 0, "test", [])])
          result = evaluate_retrieval_overlap(spans)
          assert result.loc["r1", "score"] == 0.0
  EOF
  ```

- [ ] **Step 2 : Vérifier que les tests échouent**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/test_retrieval_evaluator.py -v 2>&1 | head -10
  ```

  Attendu : `ImportError`

- [ ] **Step 3 : Implémenter retrieval_evaluator.py**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/evaluators/retrieval_evaluator.py << 'EOF'
  """Évaluateurs règles pour la qualité de retrieval (étape 2)."""

  import re
  import pandas as pd


  def evaluate_retrieval_coverage(retriever_spans: pd.DataFrame) -> pd.DataFrame:
      """Score retrieved_count / top_k pour chaque span RETRIEVER.

      Index : context.span_id. Colonnes : score (float).
      """
      records = []
      for _, row in retriever_spans.iterrows():
          span_id = row["context.span_id"]
          top_k = int(row.get("attributes.rag.top_k", 0) or 0)
          retrieved = int(row.get("attributes.rag.retrieved_count", 0) or 0)
          score = retrieved / top_k if top_k > 0 else 0.0
          records.append({"span_id": span_id, "score": round(score, 3)})
      df = pd.DataFrame(records)
      return df.set_index("span_id") if not df.empty else pd.DataFrame(columns=["score"])


  def _tokenize(text: str) -> set[str]:
      return set(re.sub(r"[^\w\s]", "", text.lower()).split()) - {"le", "la", "les", "de", "du", "des", "un", "une", "et", "en", "à", "au", "the", "a", "of", "in"}


  def _jaccard(text_a: str, text_b: str) -> float:
      a, b = _tokenize(text_a), _tokenize(text_b)
      if not a or not b:
          return 0.0
      return len(a & b) / len(a | b)


  def _collect_titles(row: pd.Series) -> list[str]:
      titles = []
      i = 0
      while True:
          col = f"attributes.retrieval.documents.{i}.document.metadata.title"
          if col not in row.index or pd.isna(row.get(col)):
              break
          titles.append(str(row[col]))
          i += 1
      return titles


  def evaluate_retrieval_overlap(retriever_spans: pd.DataFrame) -> pd.DataFrame:
      """Score Jaccard moyen entre query et titres des articles retournés.

      Index : context.span_id. Colonnes : score (float).
      """
      records = []
      for _, row in retriever_spans.iterrows():
          span_id = row["context.span_id"]
          query = str(row.get("attributes.input.value", ""))
          titles = _collect_titles(row)
          if not titles:
              score = 0.0
          else:
              scores = [_jaccard(query, title) for title in titles]
              score = round(sum(scores) / len(scores), 3)
          records.append({"span_id": span_id, "score": score})
      df = pd.DataFrame(records)
      return df.set_index("span_id") if not df.empty else pd.DataFrame(columns=["score"])
  EOF
  ```

- [ ] **Step 4 : Lancer les tests**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/test_retrieval_evaluator.py -v
  ```

  Attendu : `11 passed`

---

## Task 6 : generation_evaluator.py (TDD)

**Fichiers :**
- Créer : `~/infra/stacks/monitoring/eval/evaluators/generation_evaluator.py`
- Créer : `~/infra/stacks/monitoring/eval/tests/test_generation_evaluator.py`

Le LLM-as-judge utilise `arize-phoenix-evals`. Mais phoenix-evals n'est pas encore installé sur le VPS — les tests mockent les évaluateurs pour vérifier la logique de préparation des données et de post-traitement des résultats.

Les spans LLM ont :
- `context.span_id`
- `context.trace_id`
- `attributes.input.value` — prompt complet envoyé au LLM
- `attributes.output.value` — complétion générée

Les spans RETRIEVER (même trace) fournissent le contexte pour l'évaluation d'hallucination.

- [ ] **Step 1 : Écrire les tests**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/tests/test_generation_evaluator.py << 'EOF'
  import pandas as pd
  import pytest
  from unittest.mock import patch, MagicMock
  from evaluators.generation_evaluator import (
      prepare_generation_dataframe,
      parse_eval_results,
  )


  def make_llm_span(span_id: str, trace_id: str, prompt: str, completion: str) -> dict:
      return {
          "context.span_id": span_id,
          "context.trace_id": trace_id,
          "attributes.input.value": prompt,
          "attributes.output.value": completion,
      }


  def make_retriever_span(span_id: str, trace_id: str, titles: list[str]) -> dict:
      row = {"context.span_id": span_id, "context.trace_id": trace_id}
      for i, t in enumerate(titles):
          row[f"attributes.retrieval.documents.{i}.document.metadata.title"] = t
          row[f"attributes.retrieval.documents.{i}.document.content"] = f"Contenu de {t}"
      return row


  class TestPrepareGenerationDataframe:
      def test_basic_columns_present(self):
          llm_spans = pd.DataFrame([make_llm_span("l1", "t1", "Bonjour ?", "Bonjour !")])
          retriever_spans = pd.DataFrame([make_retriever_span("r1", "t1", ["Article A"])])
          df = prepare_generation_dataframe(llm_spans, retriever_spans)
          assert "input" in df.columns
          assert "output" in df.columns
          assert "reference" in df.columns
          assert df.index[0] == "l1"

      def test_input_output_mapping(self):
          llm_spans = pd.DataFrame([make_llm_span("l1", "t1", "question ?", "réponse")])
          retriever_spans = pd.DataFrame(columns=["context.span_id", "context.trace_id"])
          df = prepare_generation_dataframe(llm_spans, retriever_spans)
          assert df.loc["l1", "input"] == "question ?"
          assert df.loc["l1", "output"] == "réponse"

      def test_reference_built_from_retriever(self):
          llm_spans = pd.DataFrame([make_llm_span("l1", "t1", "q", "r")])
          retriever_spans = pd.DataFrame([make_retriever_span("r1", "t1", ["Article A", "Article B"])])
          df = prepare_generation_dataframe(llm_spans, retriever_spans)
          assert "Article A" in df.loc["l1", "reference"]
          assert "Article B" in df.loc["l1", "reference"]

      def test_no_retriever_span_empty_reference(self):
          llm_spans = pd.DataFrame([make_llm_span("l1", "t1", "q", "r")])
          retriever_spans = pd.DataFrame(columns=["context.span_id", "context.trace_id"])
          df = prepare_generation_dataframe(llm_spans, retriever_spans)
          assert df.loc["l1", "reference"] == ""


  class TestParseEvalResults:
      def test_maps_hallucination_labels(self):
          idx = pd.Index(["l1", "l2"], name="span_id")
          raw = pd.DataFrame({
              "label": ["hallucinated", "factual"],
              "score": [0.0, 1.0],
          }, index=idx)
          result = parse_eval_results(raw, eval_name="hallucination")
          assert result.loc["l1", "label"] == "hallucinated"
          assert result.loc["l2", "label"] == "factual"
          assert result.loc["l1", "score"] == 0.0

      def test_maps_relevance_labels(self):
          idx = pd.Index(["l1"], name="span_id")
          raw = pd.DataFrame({"label": ["relevant"], "score": [4.0]}, index=idx)
          result = parse_eval_results(raw, eval_name="relevance")
          assert result.loc["l1", "label"] == "relevant"
  EOF
  ```

- [ ] **Step 2 : Vérifier que les tests échouent**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/test_generation_evaluator.py -v 2>&1 | head -10
  ```

  Attendu : `ImportError`

- [ ] **Step 3 : Implémenter generation_evaluator.py**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/evaluators/generation_evaluator.py << 'EOF'
  """Évaluateur LLM-as-judge pour la qualité de génération (étape 3).

  Utilise arize-phoenix-evals (HallucinationEvaluator, RelevanceEvaluator).
  """

  import logging
  import pandas as pd
  from config import EVAL_LLM_BASE_URL, EVAL_LLM_MODEL

  logger = logging.getLogger(__name__)


  def _collect_reference(retriever_row: pd.Series) -> str:
      """Concatène les contenus des documents récupérés en une seule chaîne."""
      parts = []
      i = 0
      while True:
          col = f"attributes.retrieval.documents.{i}.document.content"
          title_col = f"attributes.retrieval.documents.{i}.document.metadata.title"
          if col not in retriever_row.index or pd.isna(retriever_row.get(col)):
              break
          title = retriever_row.get(title_col, f"Document {i}")
          parts.append(f"[{title}] {retriever_row[col]}")
          i += 1
      return "\n\n".join(parts)


  def prepare_generation_dataframe(
      llm_spans: pd.DataFrame,
      retriever_spans: pd.DataFrame,
  ) -> pd.DataFrame:
      """Prépare un DataFrame au format attendu par phoenix-evals.

      Index : context.span_id (spans LLM).
      Colonnes : input, output, reference.
      """
      records = []
      for _, llm in llm_spans.iterrows():
          span_id = llm["context.span_id"]
          trace_id = llm["context.trace_id"]

          parent_retriever = retriever_spans[
              retriever_spans["context.trace_id"] == trace_id
          ]
          reference = (
              _collect_reference(parent_retriever.iloc[0])
              if not parent_retriever.empty
              else ""
          )
          records.append({
              "span_id": span_id,
              "input": str(llm.get("attributes.input.value", "")),
              "output": str(llm.get("attributes.output.value", "")),
              "reference": reference,
          })

      df = pd.DataFrame(records)
      return df.set_index("span_id") if not df.empty else pd.DataFrame(
          columns=["input", "output", "reference"]
      )


  def parse_eval_results(raw_df: pd.DataFrame, eval_name: str) -> pd.DataFrame:
      """Normalise la sortie de run_evals() en DataFrame score/label.

      Index : span_id. Colonnes : score (float), label (str).
      """
      return raw_df[["score", "label"]].copy()


  def run_generation_evals(prepared_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
      """Exécute HallucinationEvaluator et RelevanceEvaluator via arize-phoenix-evals.

      Retourne {"hallucination": df, "relevance": df} avec colonnes score/label.
      """
      from phoenix.evals import (
          HallucinationEvaluator,
          RelevanceEvaluator,
          OpenAIModel,
          run_evals,
      )

      model = OpenAIModel(
          model=EVAL_LLM_MODEL,
          base_url=EVAL_LLM_BASE_URL,
          api_key="EMPTY",
      )

      evaluators = [HallucinationEvaluator(model), RelevanceEvaluator(model)]
      results = run_evals(
          dataframe=prepared_df,
          evaluators=evaluators,
          provide_explanation=False,
          concurrency=2,
      )

      hallucination_raw, relevance_raw = results
      return {
          "hallucination": parse_eval_results(hallucination_raw, "hallucination"),
          "relevance": parse_eval_results(relevance_raw, "relevance"),
      }
  EOF
  ```

- [ ] **Step 4 : Lancer les tests (sans phoenix-evals installé — les tests n'en ont pas besoin)**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/test_generation_evaluator.py -v
  ```

  Attendu : `8 passed`

---

## Task 7 : eval_worker.py (TDD)

**Fichiers :**
- Créer : `~/infra/stacks/monitoring/eval/eval_worker.py`
- Créer : `~/infra/stacks/monitoring/eval/tests/test_eval_worker.py`

- [ ] **Step 1 : Écrire les tests**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/tests/test_eval_worker.py << 'EOF'
  import pandas as pd
  import pytest
  from datetime import datetime, timezone, timedelta
  from unittest.mock import MagicMock, patch
  from eval_worker import filter_recent_spans, group_spans_by_kind


  def make_span(span_id: str, kind: str, minutes_ago: int = 10) -> dict:
      start = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
      return {
          "context.span_id": span_id,
          "context.trace_id": "trace-1",
          "attributes.openinference.span.kind": kind,
          "start_time": start,
      }


  class TestFilterRecentSpans:
      def test_keeps_recent_spans(self):
          df = pd.DataFrame([make_span("s1", "AGENT", minutes_ago=5)])
          result = filter_recent_spans(df, lookback_minutes=60)
          assert len(result) == 1

      def test_drops_old_spans(self):
          df = pd.DataFrame([make_span("s1", "AGENT", minutes_ago=120)])
          result = filter_recent_spans(df, lookback_minutes=60)
          assert len(result) == 0

      def test_empty_dataframe(self):
          df = pd.DataFrame(columns=["context.span_id", "start_time", "attributes.openinference.span.kind"])
          result = filter_recent_spans(df, lookback_minutes=60)
          assert result.empty


  class TestGroupSpansByKind:
      def test_groups_correctly(self):
          df = pd.DataFrame([
              make_span("s1", "AGENT"),
              make_span("s2", "TOOL"),
              make_span("s3", "RETRIEVER"),
              make_span("s4", "LLM"),
          ])
          groups = group_spans_by_kind(df)
          assert len(groups["agent"]) == 1
          assert len(groups["tool"]) == 1
          assert len(groups["retriever"]) == 1
          assert len(groups["llm"]) == 1

      def test_missing_kind_returns_empty(self):
          df = pd.DataFrame([make_span("s1", "AGENT")])
          groups = group_spans_by_kind(df)
          assert groups["tool"].empty
          assert groups["retriever"].empty

      def test_unknown_kind_ignored(self):
          df = pd.DataFrame([make_span("s1", "CHAIN")])
          groups = group_spans_by_kind(df)
          assert all(v.empty for v in groups.values())
  EOF
  ```

- [ ] **Step 2 : Vérifier que les tests échouent**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/test_eval_worker.py -v 2>&1 | head -10
  ```

  Attendu : `ImportError`

- [ ] **Step 3 : Implémenter eval_worker.py**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/eval_worker.py << 'EOF'
  """Orchestrateur principal du cycle d'évaluation Phoenix.

  1. Fetch spans récents depuis Phoenix
  2. Règles : tool_evaluator + retrieval_evaluator
  3. LLM-judge : generation_evaluator
  4. Post annotations via px.Client().log_evaluations()
  """

  import logging
  import sys
  from datetime import datetime, timedelta, timezone

  import pandas as pd

  from config import (
      EVAL_LOOKBACK_MINUTES,
      PHOENIX_ENDPOINT,
      PHOENIX_PROJECT_NAME,
  )
  from evaluators.tool_evaluator import evaluate_tool_used, evaluate_tool_relevance
  from evaluators.retrieval_evaluator import (
      evaluate_retrieval_coverage,
      evaluate_retrieval_overlap,
  )
  from evaluators.generation_evaluator import (
      prepare_generation_dataframe,
      run_generation_evals,
  )

  logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [eval-worker] %(levelname)s %(message)s",
  )
  logger = logging.getLogger(__name__)


  def filter_recent_spans(df: pd.DataFrame, lookback_minutes: int) -> pd.DataFrame:
      """Conserve uniquement les spans démarrés dans les lookback_minutes dernières minutes."""
      if df.empty:
          return df
      cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
      start_col = "start_time"
      if start_col not in df.columns:
          return df
      times = pd.to_datetime(df[start_col], utc=True)
      return df[times >= cutoff].reset_index(drop=True)


  def group_spans_by_kind(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
      """Sépare le DataFrame en sous-DataFrames par openinference.span.kind."""
      kind_col = "attributes.openinference.span.kind"
      empty = pd.DataFrame()
      if kind_col not in df.columns:
          return {"agent": empty, "tool": empty, "retriever": empty, "llm": empty}

      def subset(kind: str) -> pd.DataFrame:
          mask = df[kind_col].str.upper() == kind.upper()
          return df[mask].reset_index(drop=True)

      return {
          "agent": subset("AGENT"),
          "tool": subset("TOOL"),
          "retriever": subset("RETRIEVER"),
          "llm": subset("LLM"),
      }


  def _log_eval(client, eval_name: str, result_df: pd.DataFrame) -> None:
      """Poste un DataFrame d'évaluation dans Phoenix."""
      if result_df.empty:
          logger.info("  [%s] aucun span à annoter", eval_name)
          return
      from phoenix.trace import SpanEvaluations

      result_df.index.name = "span_id"
      client.log_evaluations(SpanEvaluations(eval_name=eval_name, dataframe=result_df))
      logger.info("  [%s] %d annotations postées", eval_name, len(result_df))


  def run(client=None) -> None:
      import phoenix as px

      if client is None:
          client = px.Client(endpoint=PHOENIX_ENDPOINT)

      logger.info("Fetching spans depuis Phoenix [%s] projet=%s ...", PHOENIX_ENDPOINT, PHOENIX_PROJECT_NAME)
      all_spans = client.get_spans_dataframe(project_name=PHOENIX_PROJECT_NAME)

      if all_spans is None or all_spans.empty:
          logger.info("Aucun span trouvé — arrêt.")
          return

      recent = filter_recent_spans(all_spans, EVAL_LOOKBACK_MINUTES)
      logger.info("%d spans récents (fenêtre %d min)", len(recent), EVAL_LOOKBACK_MINUTES)

      if recent.empty:
          logger.info("Aucun span récent — arrêt.")
          return

      groups = group_spans_by_kind(recent)
      agent_spans = groups["agent"]
      tool_spans = groups["tool"]
      retriever_spans = groups["retriever"]
      llm_spans = groups["llm"]

      logger.info(
          "Répartition — AGENT:%d TOOL:%d RETRIEVER:%d LLM:%d",
          len(agent_spans), len(tool_spans), len(retriever_spans), len(llm_spans),
      )

      # Étape 1 — Sélection outil
      if not agent_spans.empty:
          _log_eval(client, "tool_used", evaluate_tool_used(agent_spans, tool_spans))
      if not tool_spans.empty:
          _log_eval(client, "tool_relevance", evaluate_tool_relevance(agent_spans, tool_spans))

      # Étape 2 — Retrieval
      if not retriever_spans.empty:
          _log_eval(client, "retrieval_coverage", evaluate_retrieval_coverage(retriever_spans))
          _log_eval(client, "retrieval_overlap", evaluate_retrieval_overlap(retriever_spans))

      # Étape 3 — Génération (LLM-judge)
      if not llm_spans.empty:
          prepared = prepare_generation_dataframe(llm_spans, retriever_spans)
          if not prepared.empty:
              try:
                  gen_results = run_generation_evals(prepared)
                  for eval_name, df in gen_results.items():
                      _log_eval(client, eval_name, df)
              except Exception as exc:
                  logger.error("LLM-judge échoué : %s", exc)

      logger.info("Cycle d'évaluation terminé.")


  if __name__ == "__main__":
      try:
          run()
      except Exception as exc:
          logger.error("Erreur fatale : %s", exc)
          sys.exit(1)
  EOF
  ```

- [ ] **Step 4 : Lancer les tests**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/test_eval_worker.py -v
  ```

  Attendu : `8 passed`

- [ ] **Step 5 : Lancer tous les tests**

  ```bash
  cd ~/infra/stacks/monitoring/eval
  PYTHONPATH=. python3 -m pytest tests/ -v
  ```

  Attendu : `27 passed`

---

## Task 8 : requirements.txt + Dockerfile

**Fichiers :**
- Créer : `~/infra/stacks/monitoring/eval/requirements.txt`
- Créer : `~/infra/stacks/monitoring/eval/Dockerfile`

- [ ] **Step 1 : Créer requirements.txt**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/requirements.txt << 'EOF'
  arize-phoenix>=4.0.0
  arize-phoenix-evals>=0.17.0
  pandas>=2.0.0
  openai>=1.0.0
  pytest>=8.0.0
  EOF
  ```

- [ ] **Step 2 : Créer le Dockerfile**

  ```bash
  cat > ~/infra/stacks/monitoring/eval/Dockerfile << 'EOF'
  FROM python:3.12-slim

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  # Smoke test à la construction : imports et tests unitaires
  RUN PYTHONPATH=/app python3 -m pytest tests/ -q --tb=short

  CMD ["python3", "eval_worker.py"]
  EOF
  ```

- [ ] **Step 3 : Builder l'image (hors réseau Docker monitoring)**

  ```bash
  ssh ubuntu@51.255.206.255
  cd ~/infra/stacks/monitoring
  docker build -t eval-worker:local ./eval
  ```

  Attendu : `27 passed` dans les logs de build, puis `Successfully built`.

---

## Task 9 : Mise à jour docker-compose.yml

**Fichiers :**
- Modifier : `~/infra/stacks/monitoring/docker-compose.yml`

- [ ] **Step 1 : Ajouter le service eval-worker**

  Ouvrir `~/infra/stacks/monitoring/docker-compose.yml` et ajouter après le service `otelcol` :

  ```yaml
    eval-worker:
      build: ./eval
      image: eval-worker:local
      container_name: eval-worker
      networks: [will-vps-net]
      environment:
        PHOENIX_ENDPOINT: "http://phoenix:6006"
        PHOENIX_PROJECT_NAME: "newsfoundry"
        EVAL_LLM_BASE_URL: "${EVAL_LLM_BASE_URL}"
        EVAL_LLM_MODEL: "${EVAL_LLM_MODEL}"
        EVAL_LOOKBACK_MINUTES: "60"
      depends_on:
        phoenix:
          condition: service_healthy
      profiles: ["eval"]
      restart: "no"
  ```

- [ ] **Step 2 : Valider la syntaxe du compose**

  ```bash
  cd ~/infra/stacks/monitoring
  docker compose --profile eval config --quiet
  ```

  Attendu : aucune erreur.

- [ ] **Step 3 : Test run manuel**

  ```bash
  cd ~/infra/stacks/monitoring
  docker compose --profile eval run --rm eval-worker
  ```

  Attendu dans les logs :
  ```
  [eval-worker] INFO Fetching spans depuis Phoenix ...
  [eval-worker] INFO X spans récents (fenêtre 60 min)
  [eval-worker] INFO Cycle d'évaluation terminé.
  ```

  Si Phoenix n'a pas encore de spans newsfoundry : `Aucun span trouvé — arrêt.` est aussi acceptable.

---

## Task 10 : Cron VPS

**Fichiers :** crontab système ubuntu.

- [ ] **Step 1 : Créer le fichier de log**

  ```bash
  ssh ubuntu@51.255.206.255
  sudo touch /var/log/eval-worker.log
  sudo chown ubuntu:ubuntu /var/log/eval-worker.log
  ```

- [ ] **Step 2 : Ajouter l'entrée cron**

  ```bash
  crontab -e
  ```

  Ajouter la ligne :
  ```
  */30 * * * * cd /home/ubuntu/infra/stacks/monitoring && docker compose --profile eval run --rm eval-worker >> /var/log/eval-worker.log 2>&1
  ```

  Sauvegarder (`:wq` si vim, `Ctrl+O Ctrl+X` si nano).

- [ ] **Step 3 : Vérifier l'entrée cron**

  ```bash
  crontab -l | grep eval-worker
  ```

  Attendu : la ligne ci-dessus apparaît.

- [ ] **Step 4 : Forcer un run immédiat pour vérifier les logs**

  ```bash
  cd /home/ubuntu/infra/stacks/monitoring && docker compose --profile eval run --rm eval-worker >> /var/log/eval-worker.log 2>&1
  tail -30 /var/log/eval-worker.log
  ```

  Attendu : logs du cycle d'évaluation sans erreur fatale.

---

## Task 11 : Vérification end-to-end dans Phoenix UI

- [ ] **Step 1 : Déclencher une inférence depuis le frontend**

  Envoyer un message chat depuis l'UI NewsFoundry (ex: "Quelles sont les actus du jour ?") pour générer des spans dans Phoenix.

- [ ] **Step 2 : Attendre la propagation des spans**

  Attendre ~30 secondes, puis vérifier dans Phoenix UI (`https://phoenix.willisback.fr`) que les spans AGENT/TOOL/LLM apparaissent sous le projet `newsfoundry`.

- [ ] **Step 3 : Lancer manuellement l'eval-worker**

  ```bash
  ssh ubuntu@51.255.206.255
  cd ~/infra/stacks/monitoring
  docker compose --profile eval run --rm eval-worker
  ```

- [ ] **Step 4 : Vérifier les annotations dans Phoenix UI**

  Dans Phoenix → projet `newsfoundry` → onglet **Traces** → cliquer sur une trace → vérifier la présence des évaluations :
  - `tool_used` sur le span AGENT
  - `tool_relevance` sur le span TOOL
  - `retrieval_coverage` et `retrieval_overlap` sur le span RETRIEVER (si press_review)
  - `hallucination` et `relevance` sur le span LLM

  Les annotations doivent apparaître dans la colonne **Evaluations** de chaque span.

- [ ] **Step 5 : Vérifier le dataset Phoenix**

  Dans Phoenix → **Datasets & Experiments** → les traces annotées sont disponibles pour constitution d'un dataset d'entraînement.

---

## Notes de déploiement

- Le fichier `.env` dans `~/infra/stacks/monitoring/` n'est **pas versionné** (contient l'URL Tailscale du vLLM). Le `.env.example` est versionné.
- Pour mettre à jour l'image après modification du code : `docker build -t eval-worker:local ./eval` puis le prochain run cron utilisera la nouvelle image.
- Pour changer l'intervalle cron : `crontab -e` et modifier `*/30` (ex: `*/15` pour toutes les 15 min).
- Pour désactiver temporairement : commenter la ligne cron avec `#`.
