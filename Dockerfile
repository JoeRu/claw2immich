FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY pyproject.toml uv.lock* ./

RUN pip install --no-cache-dir \
    "httpx>=0.28.1" \
    "mcp[cli]>=1.26.0"

COPY main.py ./
COPY claw2immich ./claw2immich
COPY docs ./docs

CMD ["python", "main.py"]
