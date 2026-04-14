FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps used by Pillow and postgres drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (production only, no dev group)
RUN uv sync --no-dev --frozen

# Copy application code
COPY . ./

# Ensure static directories exist
RUN mkdir -p /app/static/photos

EXPOSE 8000

# Run directly from the venv
CMD [".venv/bin/python", "app_src/run_main.py"]
