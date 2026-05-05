FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir --user -r requirements-prod.txt

FROM python:3.11-slim AS final

WORKDIR /app

ARG UID=1000
ARG GID=1000

RUN groupadd -g $GID appgroup && \
    useradd -u $UID -g appgroup --create-home --shell /bin/bash appuser && \
    chown -R appuser:appgroup /app

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

COPY --chown=appuser:appgroup . .

RUN chmod +x /app/startup.sh && \
    mkdir -p /app/data/characters \
    && mkdir -p /app/data/materials \
    && mkdir -p /app/data/conversations \
    && mkdir -p /app/data/uploads/avatars \
    && mkdir -p /app/data/uploads/backgrounds

EXPOSE 8000

ENV APP_ENV=prod \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost', 8000); conn.request('GET', '/health'); r = conn.getresponse(); print(r.read().decode() if r.status == 200 else 'FAIL'); conn.close()" || exit 1

CMD ["/app/startup.sh"]
