"""
Combine the providers into one consistent set of prices and save it.

Toman is the primary unit inside Iran, so the free-market dollar rate
(``usd`` in Toman) is the bridge between the two units:

* gold and coins come in Toman → USD = Toman / dollar rate
* crypto comes in USD          → Toman = USD × dollar rate
* fiat: Toman from the Iranian market when available, otherwise
  official cross rate × dollar rate; USD is always the official cross rate.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from . import catalog
from .models import Asset, PriceHistory
from .providers import (
    IRAN_PROVIDERS,
    CoinGeckoProvider,
    DemoProvider,
    ExchangeRateProvider,
    NobitexProvider,
    ProviderError,
    Quote,
)

logger = logging.getLogger(__name__)

CACHE_KEY = "prices:all:v1"


def sync_assets() -> int:
    """Create or update Asset rows from the catalog. Returns the number of assets."""
    for order, definition in enumerate(catalog.ALL_ASSETS):
        Asset.objects.update_or_create(
            slug=definition.slug,
            defaults={
                "category": definition.category,
                "name_fa": definition.name_fa,
                "name_en": definition.name_en,
                "symbol": definition.symbol,
                "unit": definition.unit,
                "sort_order": order,
            },
        )
    return len(catalog.ALL_ASSETS)


def _safe_fetch(provider) -> dict[str, Quote]:
    try:
        quotes = provider.fetch()
        logger.info("%s returned %d quotes", provider.name, len(quotes))
        return quotes
    except ProviderError as exc:
        logger.warning("Provider failed: %s", exc)
        return {}


def collect_quotes(providers: dict | None = None) -> tuple[dict[str, Quote], dict[str, str]]:
    """
    Fetch every source and merge the results.
    ``providers`` lets tests inject fakes: keys ``iran``, ``fallback_usd``, ``fx``, ``crypto``.
    Returns ``(quotes, sources)`` where ``sources`` maps slug → provider name.
    """
    if providers is None:
        if settings.PRICE_DEMO_MODE:
            demo = DemoProvider()
            providers = {"iran": demo, "crypto": demo}
        else:
            iran_cls = IRAN_PROVIDERS.get(settings.IRAN_PROVIDER, IRAN_PROVIDERS["brsapi"])
            providers = {
                "iran": iran_cls(),
                "fallback_usd": NobitexProvider(),
                "fx": ExchangeRateProvider(),
                "crypto": CoinGeckoProvider(),
            }

    def fetch(key):
        provider = providers.get(key)
        return (_safe_fetch(provider), provider.name) if provider else ({}, "")

    iran, iran_name = fetch("iran")
    fx, fx_name = fetch("fx")
    crypto, crypto_name = fetch("crypto")

    quotes: dict[str, Quote] = {}
    sources: dict[str, str] = {}

    # 1. The dollar rate in Toman: the bridge between both units.
    usd_toman = iran.get("usd").toman if iran.get("usd") else None
    usd_source = iran_name
    usd_change = iran["usd"].change_24h if iran.get("usd") else None
    if not usd_toman:
        fallback, usd_source = fetch("fallback_usd")
        if fallback.get("usd"):
            usd_toman, usd_change = fallback["usd"].toman, fallback["usd"].change_24h
    if usd_toman:
        quotes["usd"] = Quote(toman=usd_toman, usd=Decimal(1), change_24h=usd_change)
        sources["usd"] = usd_source
    else:
        logger.error("No dollar rate from any source; Toman/USD conversions skipped")

    for definition in catalog.ALL_ASSETS:
        slug = definition.slug
        if slug == "usd":
            continue
        local, official, coin = iran.get(slug), fx.get(slug), crypto.get(slug)
        quote = Quote()

        if definition.category == catalog.CRYPTO and coin and coin.usd is not None:
            quote.usd, quote.change_24h = coin.usd, coin.change_24h
            if usd_toman:
                quote.toman = coin.usd * usd_toman
            sources[slug] = crypto_name

        elif definition.category == catalog.FIAT:
            if official and official.usd:
                quote.usd = official.usd
            if local and local.toman:
                quote.toman, quote.change_24h = local.toman, local.change_24h
                sources[slug] = iran_name
            elif official and official.usd and usd_toman:
                quote.toman = official.usd * usd_toman
                sources[slug] = fx_name
            if quote.usd is None and quote.toman and usd_toman:
                quote.usd = quote.toman / usd_toman

        elif definition.category == catalog.GOLD:
            source = local if (local and (local.toman or local.usd)) else official
            if source:
                quote.toman, quote.usd, quote.change_24h = source.toman, source.usd, source.change_24h
                sources[slug] = iran_name if source is local else fx_name
                if quote.toman is None and quote.usd and usd_toman:
                    quote.toman = quote.usd * usd_toman
                if quote.usd is None and quote.toman and usd_toman:
                    quote.usd = quote.toman / usd_toman

        if quote.toman is not None or quote.usd is not None:
            quotes[slug] = quote

    return quotes, sources


def _change_from_history(asset: Asset, now) -> Decimal | None:
    old = (
        asset.history.filter(recorded_at__lte=now - timedelta(hours=24))
        .order_by("-recorded_at")
        .values_list("price_toman", flat=True)
        .first()
    )
    if old and asset.price_toman:
        return (asset.price_toman - old) / old * 100
    return None


@transaction.atomic
def save_quotes(quotes: dict[str, Quote], sources: dict[str, str]) -> int:
    now = timezone.now()
    interval = timedelta(minutes=settings.PRICE_HISTORY_INTERVAL_MINUTES)
    assets = {a.slug: a for a in Asset.objects.filter(slug__in=quotes.keys())}
    history = []
    for slug, quote in quotes.items():
        asset = assets.get(slug)
        if asset is None:
            continue
        asset.price_toman = quote.toman.quantize(Decimal("0.01")) if quote.toman is not None else None
        asset.price_usd = quote.usd.quantize(Decimal("0.00000001")) if quote.usd is not None else None
        change = quote.change_24h if quote.change_24h is not None else _change_from_history(asset, now)
        asset.change_24h = change.quantize(Decimal("0.01")) if change is not None else None
        asset.source = sources.get(slug, "")
        asset.updated_at = now
        asset.save(update_fields=["price_toman", "price_usd", "change_24h", "source", "updated_at"])

        last = asset.history.order_by("-recorded_at").values_list("recorded_at", flat=True).first()
        if last is None or now - last >= interval:
            history.append(PriceHistory(
                asset=asset, price_toman=asset.price_toman, price_usd=asset.price_usd, recorded_at=now,
            ))
    PriceHistory.objects.bulk_create(history)
    cache.delete(CACHE_KEY)
    return len(quotes)


def update_prices(providers: dict | None = None) -> int:
    quotes, sources = collect_quotes(providers)
    return save_quotes(quotes, sources)


def prune_history() -> int:
    cutoff = timezone.now() - timedelta(days=settings.PRICE_HISTORY_DAYS)
    deleted, _ = PriceHistory.objects.filter(recorded_at__lt=cutoff).delete()
    return deleted
