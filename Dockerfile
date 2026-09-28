FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

CMD ["sh", "-c", "alembic upgrade head && python -m bin.api"]