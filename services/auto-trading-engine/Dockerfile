# Multi-stage Dockerfile for Auto-Trading Engine

# Stage 1: Builder
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
COPY services/auto-trading-engine/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
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

# Copy auto-trading-engine service
COPY services/auto-trading-engine /app/services/auto-trading-engine

# Create non-root user
RUN useradd -m -u 1000 autotradinguser && chown -R autotradinguser:autotradinguser /app
USER autotradinguser

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8005/health || exit 1

# Run the application from /app root
CMD ["python", "-m", "uvicorn", "services.auto-trading-engine.main:app", "--host", "0.0.0.0", "--port", "8005"]
