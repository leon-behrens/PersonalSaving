FROM python:3.14.9-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

WORKDIR /app

# Installing dependencies
COPY pyproject.toml uv.lock ./
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --no-install-project

# Copy and install project
COPY src/ ./src/
COPY README.md ./
RUN uv sync --frozen --no-dev --no-editable

# Run project
FROM python:3.14.9-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
# Now uvicorn can run without uv run
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
# Copy alembic
COPY alembic.ini ./
COPY alembic/ ./alembic/
# App runs as non-root user
RUN useradd --create-home appuser
USER appuser
# Start
CMD ["uvicorn", "personalsaving.app:create_app", "--factory", "--host=0.0.0.0", "--port=8000", "--proxy-headers", "--forwarded-allow-ips=127.0.0.1"]
