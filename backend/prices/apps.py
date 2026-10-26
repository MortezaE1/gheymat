from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sync_assets(sender, **kwargs):
    from .services import sync_assets

    sync_assets()


class PricesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "prices"
    verbose_name = "قیمت‌ها"

    def ready(self):
        # Keep the Asset table in step with catalog.py after every migrate.
        post_migrate.connect(_sync_assets, sender=self)
