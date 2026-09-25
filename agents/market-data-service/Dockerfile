# Multi-stage Dockerfile for Market Data Service

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY agents/market-data-service/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy shared library
COPY shared /app/shared

# Copy market data service
COPY agents/market-data-service /app/agents/market-data-service

# Create non-root user
RUN useradd -m -u 1000 marketdatauser && \
    chown -R marketdatauser:marketdatauser /app

USER marketdatauser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the service from /app root
CMD ["python", "-m", "uvicorn", "agents.market-data-service.main:app", "--host", "0.0.0.0", "--port", "8000"]
