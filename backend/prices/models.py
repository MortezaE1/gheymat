from django.db import models

from . import catalog


class Asset(models.Model):
    CATEGORY_CHOICES = [
        (catalog.GOLD, "طلا و سکه"),
        (catalog.CRYPTO, "ارز دیجیتال"),
        (catalog.FIAT, "ارز رسمی"),
    ]

    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, db_index=True)
    name_fa = models.CharField(max_length=64)
    name_en = models.CharField(max_length=64)
    symbol = models.CharField(max_length=16)
    # For gold: the unit ("هر گرم"); for fiat: the ISO country code used for the flag.
    unit = models.CharField(max_length=32, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    price_toman = models.DecimalField(max_digits=24, decimal_places=2, null=True, blank=True)
    price_usd = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    change_24h = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    source = models.CharField(max_length=32, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["category", "sort_order"]

    def __str__(self):
        return self.name_fa


class PriceHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="history")
    price_toman = models.DecimalField(max_digits=24, decimal_places=2, null=True)
    price_usd = models.DecimalField(max_digits=24, decimal_places=8, null=True)
    recorded_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["recorded_at"]
        indexes = [models.Index(fields=["asset", "recorded_at"])]

    def __str__(self):
        return f"{self.asset.slug} @ {self.recorded_at:%Y-%m-%d %H:%M}"
