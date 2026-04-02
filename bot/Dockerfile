FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir 'aiogram>=3.26.0,<4'

COPY . ./

CMD ["python", "-m", "bot"]
