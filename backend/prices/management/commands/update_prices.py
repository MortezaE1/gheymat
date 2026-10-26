from django.core.management.base import BaseCommand

from prices.services import update_prices


class Command(BaseCommand):
    help = "Fetch prices from all providers once and save them"

    def handle(self, *args, **options):
        count = update_prices()
        self.stdout.write(self.style.SUCCESS(f"{count} prices updated"))
