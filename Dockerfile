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

# Install Python dependencies (mirrors pyproject.toml)
RUN pip install --no-cache-dir \
    'fastapi>=0.111.0,<0.112' \
    'uvicorn[standard]>=0.29.0,<0.30' \
    'pydantic[email]>=2.7.1,<3' \
    'pydantic-settings>=2.2.1,<3' \
    'sqlalchemy[asyncio]>=2.0.30,<3' \
    'asyncpg>=0.29.0,<0.30' \
    'alembic>=1.13.1,<2' \
    'gunicorn>=23.0.0,<24' \
    'passlib>=1.7.4,<2' \
    'orjson>=3.10.12,<4' \
    'redis>=5.2.0,<6' \
    'python-jose[cryptography]>=3.3.0,<4' \
    'fastapi-users-db-sqlalchemy>=6.0.1,<7' \
    'pillow>=11.1.0,<12' \
    'prometheus-client>=0.21.1'

# Copy application code
COPY . ./

# Ensure static directories exist
RUN mkdir -p /app/static/photos

EXPOSE 8000

# Run via the script path so package-relative imports (e.g. `from main import ...`) resolve
CMD ["python", "app_src/run_main.py"]


