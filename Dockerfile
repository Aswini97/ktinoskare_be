# Use an Arm-compatible Python image
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (needed for Postgres and general tools)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# 1. Wait for the 'db' host to be available on port 5432
# 2. Create new migration files based on model changes
# 3. Apply migrations to the database
# 4. Start the Django development server
CMD ["sh", "-c", "until nc -z db 5432; do echo 'Waiting for database...'; sleep 2; done; python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]