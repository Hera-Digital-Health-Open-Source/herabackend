"""
Django settings for hera project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import json
import os
from pathlib import Path

from .secrets import GOOGLE_MAPS_KEY, SENTRY_SDK_DSN

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['HERA_DJANGO_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*.heradigitalhealth.com', '*']
CSRF_TRUSTED_ORIGINS = ['https://*.heradigitalhealth.com', 'https://localhost:5173']

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
    'rest_framework.authtoken',
    'drf_spectacular',
    'django_filters',
    'django_better_admin_arrayfield',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
    'django_google_maps',
    'corsheaders',
    'otp_auth',
    'user_profile',
    'infra',
    'child_health',
    'events',
    'surveys',
    'custom_user',
    'custom_notification',
    "health_center",
    "translation_glossary",
    "rangefilter",
    "text_to_speech",
    "concepts",
    "whatsapp_opt_history",
    "webhook_survey_responses",
    "hotline_ai_chatbot",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'hera.middleware.ReadLanguageFromUserProfileMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_otp.middleware.OTPMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'https://afetsaglikharitasi.org',
    'https://localhost:5173'
)
CSRF_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SAMESITE = 'None'
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'hera.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'hera.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DB_CLUSTER_JSON_STRING = os.getenv(
    "HERA_DB_SECRET", default='{"host": "", "port": "0", "dbname": "", "username": "", "password": ""}')
DB_CLUSTER_DATA = json.loads(DB_CLUSTER_JSON_STRING)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_CLUSTER_DATA['dbname'],
        'USER': DB_CLUSTER_DATA['username'],
        'PASSWORD': DB_CLUSTER_DATA['password'],
        'HOST': DB_CLUSTER_DATA['host'],
        'PORT': int(DB_CLUSTER_DATA['port']),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'HERA v2',
    'DESCRIPTION': 'Health Recording App',
    'VERSION': '0.2.0',
}


HERA_OTP_LENGTH: int = 6

LANGUAGE_COOKIE_NAME = 'hera_user_language'
LOCALE_PATHS = [
    "locale",
]

# Security Settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True


LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = 'two_factor:profile'

# Google API
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_KEY

sentry_sdk.init(
    dsn=SENTRY_SDK_DSN,
    integrations=[
        DjangoIntegration(
            transaction_style='url',
        ),
    ],
    traces_sample_rate=1.0,
    send_default_pii=True,
    auto_session_tracking=False,
)
