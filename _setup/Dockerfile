FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libcups2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files first for better caching
COPY requirements.txt /app/
COPY _setup/*.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project files
COPY . /app/

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
