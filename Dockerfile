FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY src/app ./src/app
COPY src/assistant_agent ./src/assistant_agent

RUN uv sync --frozen --no-dev

EXPOSE 7860

ENTRYPOINT ["uv", "run", "assistant-agent"]
