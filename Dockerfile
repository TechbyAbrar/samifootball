# ──────────────────────────────────────────────
# 1. Base Image: Use a minimal Python image
# ──────────────────────────────────────────────
FROM python:3.10-slim

# ──────────────────────────────────────────────
# 2. Environment Variables
# Prevents .pyc files and enables unbuffered output (for logging)
# ──────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ──────────────────────────────────────────────
# 3. Working Directory
# Sets the working directory inside the container
# ──────────────────────────────────────────────
WORKDIR /app

# ──────────────────────────────────────────────
# 4. System Dependencies
# Required for building some Python packages (e.g. psycopg2)
# ──────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────
# 5. Install Python Dependencies
# First copy requirements to leverage Docker cache
# ──────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ──────────────────────────────────────────────
# 6. Copy Project Files
# Copy the full project into the image
# ──────────────────────────────────────────────
COPY . .

# ➕ ADD THIS LINE to make python-decouple find .env file inside the container
COPY .env .env
# ──────────────────────────────────────────────
# 7. Port Configuration
# This is the port Gunicorn will run on
# ──────────────────────────────────────────────
EXPOSE 8002

# ──────────────────────────────────────────────
# 8. Default Command
# Uses Gunicorn for production-ready serving
# Replace 'yourproject' with the actual Django project name
# ──────────────────────────────────────────────
CMD ["uvicorn", "core.asgi:application", "--host", "0.0.0.0", "--port", "8002"]

