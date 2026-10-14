#!/usr/bin/env bash
# Reset Django admin password from WebApp/.env (or create superuser if missing).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy .env.example and set DJANGO_SUPERUSER_*" >&2
  exit 1
fi

set -a
# shellcheck source=/dev/null
source .env
set +a

username="${DJANGO_SUPERUSER_USERNAME:-admin}"
email="${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
password="${DJANGO_SUPERUSER_PASSWORD:-}"

if [[ -z "${password}" ]]; then
  echo "Set DJANGO_SUPERUSER_PASSWORD in .env first." >&2
  exit 1
fi

if ! docker compose ps --status running --services 2>/dev/null | grep -qx django_web; then
  echo "django_web is not running. Run: make start" >&2
  exit 1
fi

docker compose exec -T django_web python manage.py shell <<PY
from django.contrib.auth import get_user_model

User = get_user_model()
username = "${username}"
email = "${email}"
password = "${password}"

user = User.objects.filter(username=username).first()
if user:
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.email = email
    user.save()
    print(f"Password reset for Django admin user: {username}")
else:
    User.objects.create_superuser(username, email, password)
    print(f"Created Django admin user: {username}")
PY

echo ""
echo "Login at: http://localhost:\${DJANGO_PUBLISH_PORT:-8000}/admin/"
echo "Username: ${username}"
echo "Password: (value of DJANGO_SUPERUSER_PASSWORD in .env)"
