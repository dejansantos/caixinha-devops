"""
Django settings - Sistema de Gestão de Caixinha
"""
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-secret-key-troque-em-producao")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "dbbackup",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "core.middleware.AuditoriaUsuarioMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "caixinha_project.urls"

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

WSGI_APPLICATION = "caixinha_project.wsgi.application"

# --- Banco de dados (Postgres via Docker) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="caixinha"),
        "USER": config("POSTGRES_USER", default="caixinha_user"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="caixinha_pass_dev"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Backup automático (django-dbbackup) ---
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": str(BASE_DIR / "backups")}

# --- Login ---
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"

# 2FA (django-otp): ative exigindo verificação no login do admin em produção
# Ver README para o passo de ativação do TOTP no superusuário

# --- Jazzmin: tema visual do admin ---
JAZZMIN_SETTINGS = {
    "site_title": "Caixinha",
    "site_header": "Caixinha",
    "site_brand": "Gestão da Caixinha",
    "welcome_sign": "Bem-vindo à gestão da caixinha",
    "copyright": "TechService",
    "search_model": ["core.Cotista", "core.Emprestimo"],
    "topmenu_links": [
        {"name": "📊 Relatório", "url": "/dashboard/", "permissions": ["auth.view_user"]},
    ],
    "icons": {
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "core.cicloanual": "fas fa-calendar-alt",
        "core.cotista": "fas fa-user-friends",
        "core.cota": "fas fa-coins",
        "core.emprestimo": "fas fa-hand-holding-usd",
        "core.parcela": "fas fa-file-invoice-dollar",
        "core.rifamensal": "fas fa-ticket-alt",
        "core.investimento": "fas fa-chart-line",
        "core.movimentacao": "fas fa-exchange-alt",
        "core.rateio": "fas fa-balance-scale",
        "core.logauditoria": "fas fa-history",
    },
    "order_with_respect_to": [
        "core.cicloanual", "core.cotista", "core.cota",
        "core.emprestimo", "core.parcela", "core.rifamensal",
        "core.investimento", "core.movimentacao", "core.rateio", "core.logauditoria",
    ],
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-dark",
    "sidebar": "sidebar-dark-primary",
    "brand_colour": "navbar-success",
    "accent": "accent-success",
    "no_navbar_border": True,
}
