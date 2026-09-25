# Multi-stage Dockerfile for Trading Service

FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY services/trading-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
ENV PYTHONPATH=/app:$PYTHONPATH
COPY shared /app/shared
COPY services/trading-service /app/services/trading-service
RUN useradd -m -u 1000 tradinguser && chown -R tradinguser:tradinguser /app
USER tradinguser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
# Run the application from /app root
CMD ["python", "-m", "uvicorn", "services.trading-service.main:app", "--host", "0.0.0.0", "--port", "8000"]
