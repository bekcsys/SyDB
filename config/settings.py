import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
_allowed = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
if DEBUG and "*" not in _allowed:
    _allowed.append("*")
ALLOWED_HOSTS = _allowed

_django_port = os.environ.get("DJANGO_PUBLISH_PORT", "8000")
_csrf_origins = [
    o.strip()
    for o in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        f"http://localhost:{_django_port},http://127.0.0.1:{_django_port}",
    ).split(",")
    if o.strip()
]
if DEBUG:
    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        for ip in result.stdout.split():
            _csrf_origins.append(f"http://{ip}:{_django_port}")
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(_csrf_origins))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sauna_data",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "sauna_data.middleware.SaunaLoginMiddleware",
    "sauna_data.middleware.FriendlyDatabaseErrorMiddleware",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "sauna_tests"),
        "USER": os.environ.get("POSTGRES_USER", "sauna_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "change_me"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Chicago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_DIR = BASE_DIR / "data"
IMPORT_PENDING_DIR = DATA_DIR / "import_pending"
ARCHIVE_MIGRATED_DIR = DATA_DIR / "archive" / "db_migrated"
ARCHIVE_FAILED_DIR = DATA_DIR / "archive" / "import_failed"
IMPORT_LOG_DIR = DATA_DIR / "logs"
MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "qc_media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 180 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 180 * 1024 * 1024
QC_REPORT_BUCKET = os.environ.get("QC_REPORT_BUCKET", "sauna-qc-private")

DEFAULT_TESTER_NAME = os.environ.get("DEFAULT_TESTER_NAME", "")
DEFAULT_RUN_DURATION_MIN = int(os.environ.get("DEFAULT_RUN_DURATION_MIN", "90"))
DEFAULT_TARGET_TEMPERATURE_F = float(
    os.environ.get("DEFAULT_TARGET_TEMPERATURE_F", "150")
)
