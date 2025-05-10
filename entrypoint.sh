#!/bin/bash
set -e

# Django tasks
echo "Running migrations..."
python manage.py migrate --noinput

echo "Initializing default roles..."
python manage.py init_roles

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting server on port ${DJANGO_PORT}..."
exec python manage.py runserver 0.0.0.0:${DJANGO_PORT}
