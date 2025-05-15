import os
from core.get_env import getenv_bool, getenv_int, getenv_list
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

WSGI_APPLICATION = 'core.wsgi.application'
AUTH_USER_MODEL = 'profile_auth.User'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'rest_framework',
    'corsheaders',
    'rest_framework.authtoken',
    'django_filters',

    'profile_auth.apps.ProfileAuthConfig',
    'geo.apps.GeoConfig',
    'gossip.apps.GossipConfig',
    'oej.apps.OejConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATE_PATH = os.path.join(BASE_DIR, os.getenv("TEMPLATE_PATH", 'templates'))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_PATH],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]


# -----------------------Default database configuration-----------------------
POSTRGRESQL_DB = os.getenv('POSTRGRESQL_DB', False)
DATABASE_NAME = os.getenv("DATABASE_NAME", "db.sqlite3")
DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA")
if POSTRGRESQL_DB:
    default_database = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DATABASE_NAME,
        'USER': os.getenv("DATABASE_USER"),
        'PASSWORD': os.getenv("DATABASE_PASSWORD"),
        'HOST': os.getenv("DATABASE_HOST"),
        'PORT': int(os.getenv("DATABASE_PORT", 5432)),
    }
else:

    default_database = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATABASE_NAME
    }

if DATABASE_SCHEMA:
    default_database['OPTIONS'] = {  # type: ignore
        'options': f'-c search_path={DATABASE_SCHEMA}',
    }

DATABASES = {
    "default": default_database
}

IS_LOCAL = getenv_bool("IS_LOCAL", False)
# ---------------------end Default database configuration---------------------


# ---------------------------------SECURITY-----------------------------------

SECRET_KEY = 'django-insecure-jb^cklnl%994ct#=^i5t8o-356cxwr56)@p-9fu)85_8jl5$93'

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SONAR_API_KEY = os.getenv("SONAR_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_TOKENS_MAX_LENGTH = getenv_int("OPENAI_TOKENS_MAX_LENGTH", 128000)
OPENAI_ENGINE = os.getenv("OPENAI_ENGINE", "gpt-4o")

FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
V_API_FB = os.getenv("V_API_FB")

ALLOWED_HOSTS = getenv_list("ALLOWED_HOSTS", ["*"])
DEBUG = True

_CSRF_TRUSTED_ORIGINS = getenv_list("CSRF_TRUSTED_ORIGINS")
if _CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = _CSRF_TRUSTED_ORIGINS

CORS_ORIGIN_ALLOW_ALL = True
# USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_HOST = getenv_bool("USE_X_FORWARDED_HOST", True)
HTTP_X_FORWARDED_HOST = os.getenv("HTTP_X_FORWARDED_HOST")


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# -------------------------------END SECURITY---------------------------------


LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'SEARCH_PARAM': 'q',
    'DEFAULT_PERMISSION_CLASSES': (
        'api.permissions.IsFullEditorOrReadOnly',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

}
