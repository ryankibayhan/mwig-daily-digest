FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY src ./src

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "--no-dev", "python", "src/entrypoints/worker.py"]
