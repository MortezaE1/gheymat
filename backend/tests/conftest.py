import pytest


@pytest.fixture(autouse=True)
def _settings(settings):
    settings.PRICE_DEMO_MODE = False
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}
    settings.SECURE_SSL_REDIRECT = False
    from config.celery import app

    app.conf.task_always_eager = True
