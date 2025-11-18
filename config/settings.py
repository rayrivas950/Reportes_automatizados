import os
import dj_database_url  # Importar dj_database_url
from datetime import timedelta

from dotenv import load_dotenv

from pathlib import Path


load_dotenv()  # Carga las variables de entorno del archivo .env


# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production

# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "una-clave-secreta-insegura-por-defecto-para-desarrollo")


# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"


ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

# Email configuration for development
# In development, emails will be printed to the console.
# For production, this should be changed to a real email backend (e.g., SMTP).
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Application definition


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps de terceros
    "rest_framework",
    "django_filters",
    "rest_framework_simplejwt",  # Añadido para JWT
    "rest_framework_simplejwt.token_blacklist",  # Requerido para la blacklist de tokens
    "simple_history",  # Añadido para el historial de cambios
    "drf_spectacular",  # Añadido para la documentación OpenAPI/Swagger
    "corsheaders",      # Añadido para la gestión de CORS
    # Nuestras apps
    "crud_app",
]

# Configuración de Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "EXCEPTION_HANDLER": "crud_app.exceptions.custom_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # Para el admin de Django
        "rest_framework.authentication.BasicAuthentication",  # Para pruebas o admin
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/min",
        "user": "10000/min",
        "login": "20/min",  # Límite específico para intentos de login
    },
}

# Configuración de CACHES para throttling de DRF
# Usamos una caché en memoria local, adecuada para desarrollo y pruebas.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",  # Un nombre único para la caché
    }
}

# Configuración de djangorestframework-simplejwt
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),  # Token de acceso de corta duración
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # Token de refresco de larga duración
    "ROTATE_REFRESH_TOKENS": True,  # Rotar tokens de refresco para mejorar la seguridad
    "BLACKLIST_AFTER_ROTATION": True,  # Usar la lista negra para invalidar tokens en logout
}

# # Configuración de drf-spectacular para la documentación OpenAPI/Swagger
# SPECTACULAR_SETTINGS = {
#     'TITLE': 'Reportes Automatizados API',
#     'DESCRIPTION': 'API para la gestión de CRUD y automatización de reportes en Excel.',
#     'VERSION': '1.0.0',
#     'SERVE_INCLUDE_SCHEMA': False,
#     # Opciones de UI
#     'SWAGGER_UI_DIST': 'CDN',
#     'REDOC_UI_DIST': 'CDN',
# }


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",  # Añadido para el historial
]

# Configuración de CORS
# Se definen los orígenes permitidos para las peticiones.
# Esto es crucial para que el frontend (Angular) pueda comunicarse con la API.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",  # Origen para el desarrollo de Angular
    "http://127.0.0.1:4200", # Origen alternativo para el desarrollo de Angular
]


ROOT_URLCONF = "config.urls"


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


WSGI_APPLICATION = "config.wsgi.application"


# Database

# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configuración de la base de datos
# Intenta usar DATABASE_URL si está disponible (útil para entornos de producción/Docker)
# Si no, usa las variables individuales (compatibilidad con configuraciones existentes)
if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"), conn_max_age=600
        )
    }
    # Configuración de la base de datos de prueba si DATABASE_URL está presente
    if "default" in DATABASES and "NAME" in DATABASES["default"]:
        DATABASES["default"]["TEST"] = {"NAME": DATABASES["default"]["NAME"] + "_test"}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.getenv("POSTGRES_HOST"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "TEST": {
                "NAME": os.getenv("POSTGRES_DB") + "_test",  # DB separada para pruebas
            },
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuración de Logging
# Se añade una configuración robusta para el registro de eventos de la aplicación.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/debug.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",  # No queremos todos los DEBUG de Django, solo desde INFO
            "propagate": True,
        },
        "crud_app": {
            "handlers": ["console", "file"],
            "level": "DEBUG",  # Para nuestra app, queremos ver todos los detalles
            "propagate": True,
        },
    },
}
