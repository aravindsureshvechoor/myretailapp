# Infilect Data Ingestion API

Django + Celery backend for ingesting store, user, and store-user mapping CSV data.

---

## Stack

- Python 
- Django 
- Django REST Framework
- PostgreSQL
- Celery + Redis
- pandas (chunked CSV reading)

---

## Setup

### 1. Clone and install dependencies

```bash
cd infilect
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your DB credentials and Redis URL
```

### 3. Create database

```bash
createdb infilect   # or create via psql
```

### 4. Run migrations

```bash
python manage.py makemigrations ingestion
python manage.py migrate
```

### 5. Start Redis (if not running)

```bash
redis-server
```

### 6. Start Celery worker

```bash
celery -A config worker --loglevel=info
```

### 7. Start Django server

```bash
python manage.py runserver
```

---
```
