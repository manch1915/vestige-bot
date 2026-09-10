FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Snapshots and cached media live here; mount a volume to keep them.
VOLUME ["/app/data"]
ENV DB_PATH=/app/data/vestige.db \
    MEDIA_DIR=/app/data/media

RUN useradd --create-home --uid 1000 vestige && chown -R vestige:vestige /app
USER vestige

CMD ["python", "-m", "vestige"]
