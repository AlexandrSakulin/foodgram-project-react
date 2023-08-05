import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-tgaki2&8w)lt4%1%@*ui&p6c5^2!t&@p596i3_c#nl4^1y=pa$')

DEBUG = os.getenv('DEBUG', True)

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'recipes',
    'users',
    'api',
    'djoser',
    'django_filters'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram.urls'

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodgram.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': os.getenv('DB_ENGINE', default='django.db.backends.postgresql'),
#         'NAME': os.getenv('POSTGRES_DB', default='foodgram'),
#         'USER': os.getenv('POSTGRES_USER', default='foodgram_user'),
#         'PASSWORD': os.getenv('POSTGRES_PASSWORD', default='1234'),
#         'HOST': os.getenv('DB_HOST', default='localhost'),
#         'PORT': os.getenv('DB_PORT', default='5432')
#     }
# }


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

APPEND_SLASH = False

DJOSER = {
    'SERIALIZERS': {
        'user': 'api.serializers.UserReadSerializer',
        'current_user': 'api.serializers.UserReadSerializer',
    },
    'HIDE_USERS': False,
    'LOGIN_FIELD': 'email',
    'PERMISSIONS': {
        'user': ['rest_framework.permissions.IsAuthenticated'],
        'user_list': ['rest_framework.permissions.AllowAny'],
    },
}


LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

STATIC_ROOT = ''

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

MAX_LENGTH_EMAIL = 254

MAX_LENGTH_USERNAME = 150

MAX_LENGTH_AUTHOR = 200

MAX_LENGTH_CONFIRMATION_CODE = 100

MAX_LENGTH_RECIPE_NAME = 155

MAX_LENGTH_TAG_COLOR = 7

MAX_LENGTH_TAG_NAME = 200

MAX_LENGTH_TAG_SLUG = 200

MAX_LENGTH_INGREDIENT_NAME = 255

MAX_LENGTH_INGREDIENT_MEAUNIT = 155
