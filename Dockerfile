FROM python:3.12-slim

# Prevents Python from writing .pyc files and ensures output is sent directly to the console
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
# Added C-extensions, networking tools, and essential geospatial binaries (GDAL/GEOS) for PostGIS mapping
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    netcat-traditional \
    binutils \
    gdal-bin \
    libgdal-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project files securely into the active working directory container area
COPY . .

# Expose the internal port used by Daphne
EXPOSE 8000

# Default command (this is overridden by docker-compose for specific services)
# Includes validation loop to check database socket availability before migrations launch
CMD ["sh", "-c", "until nc -z db 5432; do echo 'Waiting for database...'; sleep 2; done && python manage.py migrate && daphne -b 0.0.0.0 -p 8000 ktinoskare.asgi:application"]