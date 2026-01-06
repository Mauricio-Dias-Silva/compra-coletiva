#!/bin/bash
set -e

# Run migrations
echo "Runnning Migrations..."
python manage.py migrate

# Start Gunicorn
echo "Starting Server..."
exec gunicorn projeto_compra_coletiva.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 8 --timeout 0
