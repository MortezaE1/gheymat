"""
Price providers.

Each provider fetches one external source and returns ``Quote`` objects keyed
by our own asset slug. Providers never touch the database; combining them and
saving is done in ``services.update_prices``. Every provider is independent,
so a failing source only leaves its own assets stale.

Units: Iranian sources quote in Toman (BrsApi, Navasan) or Rial (Nobitex);
everything is normalised to Toman here.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx
from django.conf import settings

from . import catalog

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


@dataclass
class Quote:
    toman: Decimal | None = None
    usd: Decimal | None = None
    change_24h: Decimal | None = None


def to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


class BaseProvider:
    name = "base"
    url = ""

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or httpx.Client(
            timeout=settings.PRICE_HTTP_TIMEOUT,
            headers={"User-Agent": "Gheymat/1.0 (+https://gheymat.ir)", "Accept": "application/json"},
        )

    def get_json(self, url: str, **params):
        try:
            response = self.client.get(url, params=params or None)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"{self.name}: {exc}") from exc

    def fetch(self) -> dict[str, Quote]:
        raise NotImplementedError


class CoinGeckoProvider(BaseProvider):
    """Crypto prices in USD with 24h change. Free, no key required."""

    name = "coingecko"
    url = "https://api.coingecko.com/api/v3/coins/markets"

    def fetch(self) -> dict[str, Quote]:
        mapping = catalog.provider_map("coingecko")
        if settings.COINGECKO_API_KEY:
            self.client.headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY
        data = self.get_json(
            self.url,
            vs_currency="usd",
            ids=",".join(mapping),
            price_change_percentage="24h",
        )
        quotes = {}
        for row in data:
            slug = mapping.get(row.get("id"))
            if slug:
                quotes[slug] = Quote(
                    usd=to_decimal(row.get("current_price")),
                    change_24h=to_decimal(row.get("price_change_percentage_24h")),
                )
        return quotes


class ExchangeRateProvider(BaseProvider):
    """International (official) FX rates against USD. Free, no key required."""

    name = "erapi"
    url = "https://open.er-api.com/v6/latest/USD"

    def fetch(self) -> dict[str, Quote]:
        data = self.get_json(self.url)
        if data.get("result") != "success":
            raise ProviderError(f"erapi: {data.get('error-type', 'unknown error')}")
        rates = data.get("rates", {})
        quotes = {}
        for code, slug in catalog.provider_map("erapi").items():
            rate = to_decimal(rates.get(code))
            if rate:
                # rates are "units per 1 USD"; price of one unit in USD is the inverse.
                quotes[slug] = Quote(usd=Decimal(1) / rate)
        return quotes


class NobitexProvider(BaseProvider):
    """USDT/IRR from Nobitex: a public fallback for the free-market dollar rate."""

    name = "nobitex"
    url = "https://api.nobitex.ir/market/stats"

    def fetch(self) -> dict[str, Quote]:
        data = self.get_json(self.url, srcCurrency="usdt", dstCurrency="rls")
        stats = (data.get("stats") or {}).get("usdt-rls") or {}
        rial = to_decimal(stats.get("latest"))
        if not rial:
            raise ProviderError("nobitex: no usdt-rls price")
        return {"usd": Quote(toman=rial / 10, change_24h=to_decimal(stats.get("dayChange")))}


class BrsApiProvider(BaseProvider):
    """
    BrsApi.ir: Iranian free-market gold, coins and currencies (prices in Toman).
    Needs ``BRSAPI_KEY``. Response shape: ``{"gold": [...], "currency": [...]}``
    where each row has ``symbol``, ``price`` and ``change_percent``.
    """

    name = "brsapi"
    url = "https://brsapi.ir/Api/Market/Gold_Currency.php"

    def fetch(self) -> dict[str, Quote]:
        if not settings.BRSAPI_KEY:
            raise ProviderError("brsapi: BRSAPI_KEY is not set")
        data = self.get_json(self.url, key=settings.BRSAPI_KEY)
        mapping = catalog.provider_map("brsapi")
        quotes = {}
        for group in ("gold", "currency"):
            for row in data.get(group, []) or []:
                slug = mapping.get(row.get("symbol"))
                if not slug:
                    continue
                price = to_decimal(row.get("price"))
                change = to_decimal(row.get("change_percent"))
                if slug == "gold_ounce":  # quoted in USD
                    quotes[slug] = Quote(usd=price, change_24h=change)
                else:
                    quotes[slug] = Quote(toman=price, change_24h=change)
        return quotes


class NavasanProvider(BaseProvider):
    """
    Navasan.tech: Iranian free-market gold, coins and currencies (Toman).
    Needs ``NAVASAN_API_KEY``. Response: ``{"usd_sell": {"value": "...", "change": ...}, ...}``.
    """

    name = "navasan"
    url = "https://api.navasan.tech/latest/"

    def fetch(self) -> dict[str, Quote]:
        if not settings.NAVASAN_API_KEY:
            raise ProviderError("navasan: NAVASAN_API_KEY is not set")
        data = self.get_json(self.url, api_key=settings.NAVASAN_API_KEY)
        quotes = {}
        for key, slug in catalog.provider_map("navasan").items():
            row = data.get(key)
            if not isinstance(row, dict):
                continue
            price = to_decimal(row.get("value"))
            change = to_decimal(row.get("change"))
            if price:
                # Navasan's "change" is absolute Toman; convert to percent.
                pct = (change / (price - change) * 100) if change is not None and price != change else None
                quotes[slug] = Quote(toman=price, change_24h=pct)
        return quotes


class DemoProvider(BaseProvider):
    """
    Plausible random-walk prices for local development and demos, used when
    ``PRICE_DEMO_MODE`` is on. Rows saved from it are marked ``source="demo"``
    and the site shows a "demo data" badge.
    """

    name = "demo"
    BASE_TOMAN = {
        "gold_18k": 7_150_000, "gold_24k": 9_530_000, "gold_melted": 30_950_000,
        "coin_emami": 78_500_000, "coin_bahar": 74_200_000, "coin_half": 41_800_000,
        "coin_quarter": 24_300_000, "coin_gerami": 12_100_000,
        "usd": 106_500, "eur": 123_800, "gbp": 141_900, "aed": 29_050, "try": 2_560,
        "cny": 14_900, "cad": 76_300, "aud": 69_800, "chf": 133_400, "jpy": 705,
        "sar": 28_400, "rub": 1_310,
    }
    BASE_USD = {
        "gold_ounce": 4_050, "bitcoin": 112_000, "ethereum": 4_050, "tether": 1,
        "bnb": 1_120, "solana": 196, "xrp": 2.55, "toncoin": 2.2, "dogecoin": 0.2,
        "cardano": 0.66, "tron": 0.31,
    }

    def __init__(self, client=None, seed: int | None = None):
        self.rng = random.Random(seed)

    def _walk(self, base) -> tuple[Decimal, Decimal]:
        change = self.rng.uniform(-3, 3)
        return Decimal(str(base * (1 + change / 100))), Decimal(str(round(change, 2)))

    def fetch(self) -> dict[str, Quote]:
        quotes = {}
        for slug, base in self.BASE_TOMAN.items():
            price, change = self._walk(base)
            quotes[slug] = Quote(toman=price.quantize(Decimal(1)), change_24h=change)
        for slug, base in self.BASE_USD.items():
            price, change = self._walk(base)
            quotes[slug] = Quote(usd=price, change_24h=Decimal(0) if slug == "tether" else change)
        quotes["tether"].usd = Decimal(1)
        return quotes


IRAN_PROVIDERS = {"brsapi": BrsApiProvider, "navasan": NavasanProvider}
