# Multi-stage Dockerfile for Technical Analyst Service

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
COPY agents/technical-analyst-service/requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Set Python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy shared library
COPY shared /app/shared

# Copy technical analyst service
COPY agents/technical-analyst-service /app/agents/technical-analyst-service

# Create non-root user
RUN useradd -m -u 1000 analystuser && \
    chown -R analystuser:analystuser /app

USER analystuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the service
CMD ["python", "-m", "uvicorn", "agents.technical_analyst_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
