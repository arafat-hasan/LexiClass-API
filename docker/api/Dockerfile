# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[dev]"

# Copy application code
COPY src/ ./src/
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 api \
    && chown -R api:api /app

USER api

# Command to run the application
CMD ["uvicorn", "lexiclass_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
