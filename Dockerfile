# Dockerfile

# Use Python 3.11 slim as base
FROM python:3.11-slim

# Install system dependencies
# libpq-dev is for PostgreSQL
# build-essential is for compiling some python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# [PYTHONJET] Configuração segura para build
ENV SECRET_KEY=temporary-build-key-for-collectstatic
ENV DATABASE_URL=sqlite://:memory:

# Set work directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Collect static files
# This will put static files in the directory configured in STATIC_ROOT (e.g., /app/staticfiles)
# We set SECRET_KEY to a dummy value because it's required for collectstatic but not used for serving
RUN python manage.py collectstatic --noinput

# Copy entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Run entrypoint
CMD ["/app/entrypoint.sh"]