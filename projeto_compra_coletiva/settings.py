# projeto_compra_coletiva/settings.py

import os
from pathlib import Path
import dj_database_url
from datetime import timedelta
from django.utils import timezone

# --- BLINDAGEM DE CONFIGURAÇÃO (O SEGREDO) ---
# Tenta usar python-decouple, mas cria um fallback seguro se não existir
# Isso impede que o site quebre se faltar o arquivo .env na nuvem
try:
    from decouple import config, Csv
except ImportError:
    def config(key, default=None, cast=None):
        val = os.environ.get(key, default)
        if val is None: return None
        if cast == bool: return val.lower() in ('true', '1', 't')
        if cast == int: return int(val)
        return val

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURANÇA ---
# Usa uma chave padrão se não encontrar no ambiente (evita erro 500 no build)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-chave-provisoria-para-build')

# DEBUG seguro: Padrão True local, mas False se a variável disser False
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS: Aceita tudo por enquanto (O PythonJet trava isso depois na injeção)
ALLOWED_HOSTS = ['*']

# CSRF: Permite que o painel do Google Cloud faça login
CSRF_TRUSTED_ORIGINS = ['https://*.run.app', 'https://*.pythonjet.app']

# --- APLICATIVOS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Ajuda no dev local
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    
    # Libs de Terceiros
    'rest_framework',
    'rest_framework_simplejwt', 
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Seus apps
    'contas',
    'ofertas',
    'compras',
    'vendedores_painel',
    'pagamentos',
    'pedidos_coletivos',
    'fiscal', # Módulo Fiscal (NFe/NFS-e)
    'comunicacao', # Módulo de E-mails e Notificações
    'logistica_app', # App de Logística (Painel Motoboy)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise: OBRIGATÓRIO estar aqui para servir estáticos na nuvem
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', 
]

ROOT_URLCONF = 'projeto_compra_coletiva.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Seus context processors (garanta que não quebram se o app falhar)
                'ofertas.context_processors.categorias_globais',
                'contas.context_processors.notificacoes_nao_lidas_globais'
            ],
        },
    },
]

WSGI_APPLICATION = 'projeto_compra_coletiva.wsgi.application'

# --- BANCO DE DADOS HÍBRIDO (LOCAL vs NUVEM) ---
CLOUD_SQL_CONNECTION_NAME = config('CLOUD_SQL_CONNECTION_NAME', default=None)

if CLOUD_SQL_CONNECTION_NAME:
    # --- PRODUÇÃO (CLOUD RUN) ---
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}',
            'NAME': config('DB_NAME', default='sysgov_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'PORT': '', # Porta vazia força Socket Unix na GCP
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
    }
else:
    # Se na nuvem via env URL, usa dj_database_url
    if config('DATABASE_URL', default=None):
        DATABASES = {
            'default': dj_database_url.config(
                default=config('DATABASE_URL'),
                conn_max_age=600
            )
        }
    else:
        # Fallback local SQLite3
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

# --- ARQUIVOS ESTÁTICOS ---
# --- ARQUIVOS ESTÁTICOS & MEDIA ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# --- GOOGLE CLOUD STORAGE (PythonJet Auto-Config) ---
GS_BUCKET_NAME = config('GS_BUCKET_NAME', default=None)

if GS_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    # STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage" # Opcional
    GS_PROJECT_ID = config('GOOGLE_CLOUD_PROJECT', default=None)
    GS_DEFAULT_ACL = "publicRead"
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"

# --- CONFIGURAÇÕES DRF & JWT ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- ALLAUTH ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
AUTH_USER_MODEL = 'contas.Usuario'
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {'username', 'email'} 
ACCOUNT_EMAIL_VERIFICATION = 'none' 
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# --- EMAIL ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.mailtrap.io')
EMAIL_PORT = config('EMAIL_PORT', default=2525, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

# --- MERCADO PAGO ---
MERCADO_PAGO_PUBLIC_KEY = config('MERCADO_PAGO_PUBLIC_KEY', default='')
MERCADO_PAGO_ACCESS_TOKEN = config('MERCADO_PAGO_ACCESS_TOKEN', default='')

# --- AI GEMINI ---
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# --- LOGÍSTICA (PYTHONJET) ---
PYTHONJET_LOGISTICS_API_KEY = config('PYTHONJET_LOGISTICS_API_KEY', default='')

# --- CELERY ---
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'

# --- OUTROS ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True