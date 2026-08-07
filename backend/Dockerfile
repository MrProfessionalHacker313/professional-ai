# ===================================================================
# Professional AI - Backend Dockerfile (Serves Built Frontend on :8000)
# ===================================================================

FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build static export
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_APP_VERSION=1.0.0
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_VERSION=$NEXT_PUBLIC_APP_VERSION
RUN npm run build

# ===================================================================
# Backend stage
# ===================================================================
FROM python:3.11-slim

LABEL maintainer="Professional AI Security Team"
LABEL description="Professional AI Backend - Security Hardened"
LABEL version="3.0.0"

# Security: Run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    openssl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pip-audit

# Copy application code
COPY backend/ ./

# Copy built frontend static output into backend for serving on :8000
COPY --from=frontend-builder /frontend/out ./frontend/out

# Create necessary directories with proper permissions
RUN mkdir -p logs uploads/documents uploads/videos && \
    chown -R appuser:appuser /app

# Security: Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Security: Disable debug mode in production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UNLIMITED_PLANS=pro,pro_yearly,max,business,enterprise,trial

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]