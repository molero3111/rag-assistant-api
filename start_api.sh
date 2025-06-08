#!/bin/bash

# Load environment variables from .env if present
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run Django migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Run Django dev server for local, Gunicorn for production
if [ "$DJANGO_ENV" = "local" ]; then
    python manage.py runserver 0.0.0.0:8000
else
    gunicorn core.wsgi:application -b 0.0.0.0:8000
fi
