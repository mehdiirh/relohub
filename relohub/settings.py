import os
from ast import literal_eval
from pathlib import Path

from .celery.config import *


def env_literal(key, _default=None):
    value = os.environ.get(key, _default)
    if value != _default:
        return eval(str(value))
    return value


def env_default(key, default):
    value = os.environ.get(key, default)
    if value:
        return value
    return default


def env_list(key):
    value = os.environ.get(key)
    if value:
        return value.split(",")
    return []


BASE_DIR = Path(__file__).resolve().parent.parent

WEBSITE_ADDRESS = os.environ.get("WEBSITE_ADDRESS", "http://localhost")

SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = env_literal("DEBUG", False)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = []
for host in ALLOWED_HOSTS:
    CSRF_TRUSTED_ORIGINS.append(f"http://{host}")
    CSRF_TRUSTED_ORIGINS.append(f"https://{host}")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # local apps
    "core",
    "user",
    "job",
    "linkedin",
]

GATEWAYS = []

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middlewares.force_change_password.ForceDefaultAdminToChangePassword",
]

ROOT_URLCONF = "relohub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "relohub.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASS"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("CACHE_URL", "redis://"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
]


GRAPHENE = {
    "RELAY_CONNECTION_MAX_LIMIT": 100,
}


# Internationalization
LANGUAGE_CODE = env_default("LANGUAGE_CODE", "en-us")
TIME_ZONE = env_default("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

# Media
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

AUTH_USER_MODEL = "user.User"

LINKEDIN_JOB_DESCRIPTION_KEYWORDS = [
    "relocation",
    "relo",
    "relocate",
    "visa",
]

LINKEDIN_JOB_DESCRIPTION_KEYWORD_COMPLEMENTS = [
    "costs",
    "allowance",
    "bonus",
    "coverage",
    "package",
    "sponsorship",
    "support",
    "assistance",
    "assistant",
    "cover",
]
