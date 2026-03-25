# Use an Arm-compatible Python image
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (needed for Postgres and general tools)
# Added: --no-install-recommends, apt-get clean, timeout, and improved error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# 1. Wait for the 'db' host to be available on port 5432 (timeout: 30s)
# 2. Create new migration files based on model changes
# 3. Apply migrations to the database
# 4. Start Daphne ASGI server (not runserver for production)
CMD ["sh", "-c", "timeout 30 bash -c 'until nc -z db 5432; do echo \"Waiting for database...\"; sleep 2; done' || true && python manage.py makemigrations && python manage.py migrate && daphne -b 0.0.0.0 -p 8000 ktinoskare.asgi:application"]