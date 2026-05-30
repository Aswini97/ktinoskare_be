# 🚜 KtinosKare Backend Development Engine

This repository houses the core Python/Django application framework for the KtinosKare tracking ecosystem. This guide details the explicit configuration steps required to spin up the thin vertical slice (Walking Skeleton) development sandbox on your local machine using containerized components.

---

## 🛠️ Local Sandbox Infrastructure Prerequisites

Ensure your local workstation has the following base engine configurations installed:

* **Docker Desktop** (with Docker Compose v2.0+)
* **Python 3.12** (for local shell validation loops)

---

## ⚡ Quick Start: 3-Step Initialization Setup

Follow this terminal command workflow sequence exactly to initialize the workspace:

### 1. Clone & Initialize the Environment Variables

Create a `.env` file in the project's root directory to seed local secrets:

```cmd
# For Windows Command Prompt or PowerShell
echo DJANGO_SECRET_KEY="django-insecure-your-hardcoded-fallback-secret-key-here" >> .env
echo DEBUG=True >> .env

```

### 2. Launch Container Infrastructure Stack

Spin up the coordinated database and caching broker network layers in the background:

```cmd
docker-compose down
docker-compose up -d --build

```

*This command launches 8 structural containers including **TimescaleDB (with PostGIS)**, **EMQX Enterprise Broker**, Redis, Daphne application hosts, and an Nginx proxy.*

### 3. Verify Container Status Line

Confirm all local ecosystem containers are running securely:

```cmd
docker-compose ps

```

---

## 🗄️ Database Schema & Extension Initializations

Once your container fleet indicates a running status loop, apply migrations to activate the spatial-temporal extensions and convert tables into hypertables:

```cmd
# Execute migrations inside the web runtime box container
docker-compose exec web python manage.py migrate

```

### 🔍 Local Port Reference Layout

To debug or monitor local transactions directly on your workbench, access these interface routes:

* 🌐 **Django REST API Server Console:** `http://localhost:8000/`
* 📊 **EMQX Management Dashboard UI:** `http://localhost:18083/` (User: `admin` | Pass: `public`)
* 🐘 **pgAdmin DB Management Tool:** `http://localhost:5050/` (User: `admin@admin.com` | Pass: `your_pgadmin_password`)
* 🗲 **Local Redis Ingest Broker Port:** Exposed on Host Port `16379` to prevent Windows socket exclusion conflicts.

---

## 🔄 Local Ingestion Pipeline Verification Loop

To mock and test the asynchronous serverless S3 ingestion webhook pipeline locally without executing live AWS calls, pass a simulated S3 Object Put Event block to your internal webhook listener via `curl` or Postman:

```cmd
curl -X POST http://localhost:8000/api/v1/internal/s3-webhook/ \
  -H "Content-Type: application/json" \
  -d "{\"Records\": [{\"s3\": {\"bucket\": {\"name\": \"ktinoscare-telemetry-bucket\"}, \"object\": {\"key\": \"telemetry/imei/869342061123456/data.csv\"}}}]}"

```

*Executing this ensures your view layer successfully calls the `boto3` client emulator, extracts positional CSV markers, passes coordinates to the boundary-safe `ST_Covers()` predicate, and registers system alert profiles smoothly.*