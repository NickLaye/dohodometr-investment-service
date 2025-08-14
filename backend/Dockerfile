# syntax=docker/dockerfile:1.6
# Multi-stage build for optimized production image
FROM python:3.12-slim as builder

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Метаданные (OCI compatible)
LABEL org.opencontainers.image.title="Dohodometr Backend API"
LABEL org.opencontainers.image.description="Investment portfolio management backend service"
LABEL org.opencontainers.image.version="${VERSION:-1.0.0}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/yourusername/dohodometr"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Dohodometr Team"
LABEL org.opencontainers.image.licenses="MIT"

# Security: Create non-root user early
RUN groupadd -r appuser && useradd -r -g appuser --uid=1001 appuser

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --user -r requirements.txt

# Production stage - minimal distroless-like image  
FROM python:3.12-slim as production

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser --uid=1001 appuser

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Security: Set secure environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    PATH="/home/appuser/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage  
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/uploads /tmp/app \
    && chown -R appuser:appuser /app /tmp/app \
    && chmod 755 /app \
    && chmod 750 /app/logs /app/uploads

# Security: Remove any potential secrets or sensitive files
RUN find /app -name "*.pyc" -delete \
    && find /app -name "__pycache__" -type d -exec rm -rf {} + \
    && rm -rf /app/.git /app/tests /app/docs \
    && rm -f /app/.env* /app/docker-compose* /app/Dockerfile*

# Switch to non-root user
USER appuser

# Security: Expose port (non-privileged)
EXPOSE 8000

# Health check with proper timeout and retries
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Security: Use exec form and run as non-root
CMD ["gunicorn", "app.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--worker-tmp-dir", "/tmp/app", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload"]
