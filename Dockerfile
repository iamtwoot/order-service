FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv sync --no-dev

CMD ["uv", "run", "python", "-m", "bin.api"]