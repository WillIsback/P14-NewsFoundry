# ── Stage 1: install dependencies ──────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
# --no-dev: exclude pytest, ruff, mkdocs from the runtime image
RUN uv sync --frozen --no-dev

# Pre-download ONNX embedding model (fastembed, évite le téléchargement au démarrage)
ENV FASTEMBED_CACHE_PATH=/app/.fastembed_cache
RUN .venv/bin/python -c "\
from llama_index.embeddings.fastembed import FastEmbedEmbedding; \
m = FastEmbedEmbedding(model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'); \
m.get_text_embedding('test')"

# ── Stage 2: minimal runtime image ─────────────────────────────────────────
FROM python:3.13-slim-bookworm

WORKDIR /app

# Create a non-root user for security
RUN adduser --disabled-password --no-create-home --uid 1001 appuser

# Copy virtual environment and ONNX model cache from builder
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --from=builder --chown=appuser:appuser /app/.fastembed_cache ./.fastembed_cache

# Copy application code
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser src/ ./src/

# Use the venv python directly (no uv in runtime)
# LLAMA_INDEX_CACHE_DIR pointe vers un répertoire accessible à appuser
# (--no-create-home → /home/appuser n'existe pas, LlamaIndex ne peut pas y écrire).
RUN mkdir -p /app/.llama_index_cache && chown appuser:appuser /app/.llama_index_cache

ENV PATH="/app/.venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  FASTEMBED_CACHE_PATH=/app/.fastembed_cache \
  LLAMA_INDEX_CACHE_DIR=/app/.llama_index_cache

COPY --chown=appuser:appuser docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys\ntry:\n urllib.request.urlopen('http://localhost:8000/')\nexcept Exception:\n sys.exit(1)"]

CMD ["./docker-entrypoint.sh"]
