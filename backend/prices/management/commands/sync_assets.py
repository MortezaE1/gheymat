from django.core.management.base import BaseCommand

from prices.services import sync_assets


class Command(BaseCommand):
    help = "Create or update tracked assets from prices/catalog.py"

    def handle(self, *args, **options):
        count = sync_assets()
        self.stdout.write(self.style.SUCCESS(f"{count} assets synced"))
