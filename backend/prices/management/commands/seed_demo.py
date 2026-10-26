import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from prices.models import Asset, PriceHistory
from prices.services import CACHE_KEY, _change_from_history, update_prices
from django.core.cache import cache


class Command(BaseCommand):
    help = "Fill the database with demo prices and a week of random-walk history (demo mode only)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, days, **options):
        if not settings.PRICE_DEMO_MODE:
            raise CommandError("Set PRICE_DEMO_MODE=1 to seed demo data.")
        PriceHistory.objects.all().delete()
        update_prices()
        PriceHistory.objects.all().delete()

        now = timezone.now()
        steps = days * 24 * 2  # one point every 30 minutes
        rows = []
        for asset in Asset.objects.exclude(price_toman=None):
            rng = random.Random(asset.slug)
            volatility = 0.004 if asset.category == "crypto" else 0.0015
            factor = 1.0
            series = []
            for i in range(steps):  # walk backwards from today's price
                series.append(factor)
                factor *= 1 + rng.gauss(0, volatility)
            for i, f in enumerate(reversed(series)):
                ratio = Decimal(str(f))
                rows.append(PriceHistory(
                    asset=asset,
                    price_toman=(asset.price_toman / ratio).quantize(Decimal("0.01")),
                    price_usd=(asset.price_usd / ratio).quantize(Decimal("0.00000001")) if asset.price_usd else None,
                    recorded_at=now - timedelta(minutes=30 * (steps - 1 - i)),
                ))
        PriceHistory.objects.bulk_create(rows, batch_size=2000)
        # Make the 24h change agree with the generated history.
        for asset in Asset.objects.exclude(price_toman=None):
            change = _change_from_history(asset, now)
            asset.change_24h = change.quantize(Decimal("0.01")) if change is not None else None
            asset.save(update_fields=["change_24h"])
        cache.delete(CACHE_KEY)
        self.stdout.write(self.style.SUCCESS(f"{len(rows)} history points created"))
