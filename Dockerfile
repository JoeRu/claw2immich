FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir httpx "mcp[cli]"

COPY main.py /app/main.py

EXPOSE 8765

CMD ["python", "main.py"]
