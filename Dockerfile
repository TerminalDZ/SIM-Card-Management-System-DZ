# syntax=docker/dockerfile:1.7

############################
# Stage 1 — builder
############################
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir=/wheels -r requirements.txt

############################
# Stage 2 — runtime
############################
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    APP_LOG_FILE=/app/logs/sim_manager.log

# Runtime utilities + permissions for serial devices
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app -g 1000 \
    && useradd -r -u 1000 -g app -d /app -s /sbin/nologin app

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY app/ ./app/
COPY data/ ./data/
COPY run.py ./

RUN mkdir -p /app/logs && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail http://127.0.0.1:${APP_PORT}/api/health || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["python", "run.py"]
