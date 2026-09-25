# Dockerfile for Technical Analyst Service (ARM64 compatible)

FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY agents/technical-analyst-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy shared library
COPY shared /app/shared

# Copy technical analyst service (rename to use underscores for Python import)
COPY agents/technical-analyst-service /app/agents/technical_analyst_service

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
