# syntax=docker/dockerfile:1
FROM python:3.12-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY chief ./chief

RUN pip install --upgrade pip \
    && pip install --no-cache-dir .[dev]

COPY tests ./tests

CMD ["pytest", "-q"]
