FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Wait for DB, run migrations, start Daphne
CMD ["sh", "-c", "timeout 30 bash -c 'until nc -z db 5432; do echo \"Waiting for database...\"; sleep 2; done' || true && python manage.py migrate && daphne -b 0.0.0.0 -p 8000 ktinoskare.asgi:application"]