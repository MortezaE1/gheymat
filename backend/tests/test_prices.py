from decimal import Decimal

import httpx
import pytest
import respx

from prices.models import Asset
from prices.providers import (
    BrsApiProvider,
    CoinGeckoProvider,
    ExchangeRateProvider,
    NavasanProvider,
    NobitexProvider,
    ProviderError,
    Quote,
)
from prices.services import collect_quotes, update_prices

pytestmark = pytest.mark.django_db


class Fake:
    def __init__(self, name, quotes=None, error=False):
        self.name, self.quotes, self.error = name, quotes or {}, error

    def fetch(self):
        if self.error:
            raise ProviderError(f"{self.name} down")
        return self.quotes


def providers(**overrides):
    base = {
        "iran": Fake("brsapi", {
            "usd": Quote(toman=Decimal(100_000), change_24h=Decimal("1.5")),
            "eur": Quote(toman=Decimal(120_000)),
            "gold_18k": Quote(toman=Decimal(7_000_000), change_24h=Decimal("-0.4")),
        }),
        "fallback_usd": Fake("nobitex", {"usd": Quote(toman=Decimal(99_000))}),
        "fx": Fake("erapi", {"eur": Quote(usd=Decimal("1.1")), "gbp": Quote(usd=Decimal("1.3"))}),
        "crypto": Fake("coingecko", {"bitcoin": Quote(usd=Decimal(100_000), change_24h=Decimal(2))}),
    }
    base.update(overrides)
    return base


def test_merge_converts_between_toman_and_usd():
    quotes, sources = collect_quotes(providers())
    assert quotes["usd"].toman == 100_000
    assert quotes["bitcoin"].toman == Decimal(100_000) * 100_000
    assert quotes["gold_18k"].usd == 70
    # Iranian-market Toman wins for fiat, the USD value is the official cross rate.
    assert quotes["eur"].toman == 120_000 and quotes["eur"].usd == Decimal("1.1")
    # No market price for GBP: derived from the cross rate.
    assert quotes["gbp"].toman == Decimal("1.3") * 100_000
    assert sources["gbp"] == "erapi" and sources["eur"] == "brsapi"


def test_dollar_falls_back_to_nobitex_when_iran_source_is_down():
    quotes, sources = collect_quotes(providers(iran=Fake("brsapi", error=True)))
    assert quotes["usd"].toman == 99_000 and sources["usd"] == "nobitex"
    assert quotes["bitcoin"].toman == Decimal(100_000) * 99_000


def test_update_saves_prices_and_history():
    update_prices(providers())
    btc = Asset.objects.get(slug="bitcoin")
    assert btc.price_usd == 100_000 and btc.change_24h == 2 and btc.source == "coingecko"
    assert btc.history.count() == 1
    update_prices(providers())  # within the history interval: no new row
    assert btc.history.count() == 1


def test_failing_source_keeps_previous_prices():
    update_prices(providers())
    update_prices(providers(crypto=Fake("coingecko", error=True)))
    assert Asset.objects.get(slug="bitcoin").price_usd == 100_000


def test_price_api(client):
    update_prices(providers())
    data = client.get("/api/prices/").json()
    assert data["usd_toman"] == 100_000 and data["is_demo"] is False
    assert {"gold", "crypto", "fiat"} == set(data["categories"])
    btc = next(a for a in data["categories"]["crypto"] if a["slug"] == "bitcoin")
    assert btc["price_toman"] == 1e10 and btc["spark"] == [1e10]
    history = client.get("/api/prices/bitcoin/history/?days=3").json()
    assert history["days"] == 3 and len(history["points"]) == 1
    assert client.get("/api/prices/nope/history/").status_code == 404


@respx.mock
def test_brsapi_parsing(settings):
    settings.BRSAPI_KEY = "k"
    respx.get(BrsApiProvider.url).mock(return_value=httpx.Response(200, json={
        "gold": [
            {"symbol": "IR_GOLD_18K", "price": 7100000, "change_percent": -0.5},
            {"symbol": "XAUUSD", "price": 4000.5, "change_percent": 0.2},
        ],
        "currency": [{"symbol": "USD", "price": "106,500", "change_percent": 1.1}],
    }))
    quotes = BrsApiProvider().fetch()
    assert quotes["gold_18k"].toman == 7_100_000
    assert quotes["gold_ounce"].usd == Decimal("4000.5")
    assert quotes["usd"].toman == 106_500


def test_brsapi_requires_key(settings):
    settings.BRSAPI_KEY = ""
    with pytest.raises(ProviderError):
        BrsApiProvider().fetch()


@respx.mock
def test_navasan_parsing(settings):
    settings.NAVASAN_API_KEY = "k"
    respx.get(NavasanProvider.url).mock(return_value=httpx.Response(200, json={
        "usd_sell": {"value": "110000", "change": 10000},
    }))
    quotes = NavasanProvider().fetch()
    assert quotes["usd"].toman == 110_000 and quotes["usd"].change_24h == 10


@respx.mock
def test_public_providers_parsing():
    respx.get(CoinGeckoProvider.url).mock(return_value=httpx.Response(200, json=[
        {"id": "bitcoin", "current_price": 100000, "price_change_percentage_24h": -1.2},
    ]))
    respx.get(ExchangeRateProvider.url).mock(return_value=httpx.Response(200, json={
        "result": "success", "rates": {"USD": 1, "EUR": 0.8},
    }))
    respx.get(NobitexProvider.url).mock(return_value=httpx.Response(200, json={
        "status": "ok", "stats": {"usdt-rls": {"latest": "1065000", "dayChange": "0.3"}},
    }))
    assert CoinGeckoProvider().fetch()["bitcoin"].change_24h == Decimal("-1.2")
    assert ExchangeRateProvider().fetch()["eur"].usd == Decimal("1.25")
    assert NobitexProvider().fetch()["usd"].toman == 106_500


@respx.mock
def test_http_error_becomes_provider_error():
    respx.get(CoinGeckoProvider.url).mock(return_value=httpx.Response(429))
    with pytest.raises(ProviderError):
        CoinGeckoProvider().fetch()
