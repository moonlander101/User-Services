# Use official Python slim image
FROM python:3.12-slim

LABEL maintainer="iran"

# Environment config
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies for Python + PostgreSQL + C extensions (needed for cryptography, psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Django port (can be overridden)
EXPOSE ${DJANGO_PORT}

# Entrypoint will run migrations and then start the server
ENTRYPOINT ["/entrypoint.sh"]
