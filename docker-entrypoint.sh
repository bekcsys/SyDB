#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
username = '${DJANGO_SUPERUSER_USERNAME}'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username,
        '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}',
        '${DJANGO_SUPERUSER_PASSWORD}',
    )
    print('Superuser created:', username)
else:
    print('Superuser already exists:', username)
"
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
