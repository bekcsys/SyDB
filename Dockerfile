FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="tempsensor-webapp" \
      org.opencontainers.image.description="Product Test Data — Django + Gunicorn"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/import_pending data/archive/db_migrated data/archive/import_failed data/logs \
    && chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
