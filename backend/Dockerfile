# ── Stage 1: install dependencies ──────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
# --no-dev: exclude pytest, ruff, mkdocs from the runtime image
RUN uv sync --frozen --no-dev

# ── Stage 2: minimal runtime image ─────────────────────────────────────────
FROM python:3.13-slim-bookworm

WORKDIR /app

# Create a non-root user for security
RUN adduser --disabled-password --no-create-home --uid 1001 appuser

# Copy only the virtual environment from the builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

# Copy application code
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser src/ ./src/

# Use the venv python directly (no uv in runtime)
ENV PATH="/app/.venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys\ntry:\n urllib.request.urlopen('http://localhost:8000/')\nexcept Exception:\n sys.exit(1)"]

CMD ["python", "src/main.py"]
