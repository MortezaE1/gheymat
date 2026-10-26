from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from . import catalog
from .models import Asset, PriceHistory
from .serializers import AssetSerializer
from .services import CACHE_KEY

SPARK_POINTS = 24


def _sparks(assets) -> dict[int, list[float]]:
    """Last 24 hours of Toman prices per asset, downsampled to SPARK_POINTS points."""
    since = timezone.now() - timedelta(hours=24)
    rows = (
        PriceHistory.objects.filter(asset__in=assets, recorded_at__gte=since)
        .order_by("recorded_at")
        .values_list("asset_id", "price_toman", "price_usd")
    )
    series = defaultdict(list)
    for asset_id, toman, usd in rows:
        value = toman if toman is not None else usd
        if value is not None:
            series[asset_id].append(float(value))
    result = {}
    for asset_id, values in series.items():
        step = max(1, len(values) // SPARK_POINTS)
        sampled = values[::step][-SPARK_POINTS:]
        if sampled[-1] != values[-1]:
            sampled.append(values[-1])
        result[asset_id] = sampled
    return result


def build_price_payload() -> dict:
    assets = list(Asset.objects.filter(is_active=True))
    data = AssetSerializer(assets, many=True, context={"sparks": _sparks(assets)}).data
    grouped = {catalog.GOLD: [], catalog.CRYPTO: [], catalog.FIAT: []}
    for row in data:
        grouped[row["category"]].append(row)
    usd = next((a for a in assets if a.slug == "usd"), None)
    updated = max((a.updated_at for a in assets if a.updated_at), default=None)
    return {
        "updated_at": updated.isoformat() if updated else None,
        "usd_toman": float(usd.price_toman) if usd and usd.price_toman else None,
        "is_demo": settings.PRICE_DEMO_MODE or any(a.source == "demo" for a in assets),
        "categories": grouped,
    }


class PriceListView(APIView):
    """All tracked prices grouped by category. Cached until the next update."""

    def get(self, request):
        payload = cache.get(CACHE_KEY)
        if payload is None:
            payload = build_price_payload()
            cache.set(CACHE_KEY, payload, timeout=settings.PRICE_UPDATE_SECONDS)
        return Response(payload)


class PriceHistoryView(APIView):
    """Price history of one asset. ``?days=`` between 1 and PRICE_HISTORY_DAYS (default 7)."""

    def get(self, request, slug):
        asset = get_object_or_404(Asset, slug=slug, is_active=True)
        try:
            days = int(request.query_params.get("days", 7))
        except ValueError:
            days = 7
        days = min(max(days, 1), settings.PRICE_HISTORY_DAYS)
        since = timezone.now() - timedelta(days=days)
        points = asset.history.filter(recorded_at__gte=since).values_list("recorded_at", "price_toman", "price_usd")
        return Response({
            "slug": asset.slug,
            "name_fa": asset.name_fa,
            "days": days,
            "points": [
                {"t": t.isoformat(), "toman": float(toman) if toman is not None else None,
                 "usd": float(usd) if usd is not None else None}
                for t, toman, usd in points
            ],
        })
