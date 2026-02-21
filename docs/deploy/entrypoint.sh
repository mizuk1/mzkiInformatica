#!/bin/bash

echo "🚀 Starting Django application (mzkiInformatica)..."

# Navigate to Django directory
cd mzkiInformatica

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "⚠️  Static files collection failed"

# Apply database migrations
echo "🗄️  Applying migrations..."
python manage.py migrate --noinput || echo "⚠️  Migrations failed"

# Run gunicorn
echo "✅ Starting Gunicorn..."
gunicorn mzkiInformatica.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 2 --timeout 120
