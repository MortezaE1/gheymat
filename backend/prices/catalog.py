"""
The list of assets the site tracks.

Adding an asset is a matter of adding a row here and running
``python manage.py sync_assets``. ``key`` fields map the asset to each
provider's own symbol; a missing key means that provider does not cover it.
"""

from dataclasses import dataclass, field

GOLD = "gold"
CRYPTO = "crypto"
FIAT = "fiat"


@dataclass(frozen=True)
class AssetDef:
    slug: str
    category: str
    name_fa: str
    name_en: str
    symbol: str
    unit: str = ""
    keys: dict = field(default_factory=dict)


GOLD_ASSETS = [
    AssetDef("gold_18k", GOLD, "طلای ۱۸ عیار", "Gold 18K", "18K", "هر گرم",
             {"brsapi": "IR_GOLD_18K", "navasan": "18ayar"}),
    AssetDef("gold_24k", GOLD, "طلای ۲۴ عیار", "Gold 24K", "24K", "هر گرم",
             {"brsapi": "IR_GOLD_24K"}),
    AssetDef("gold_melted", GOLD, "طلای آب‌شده", "Melted gold", "MLT", "هر مثقال",
             {"brsapi": "IR_GOLD_MELTED", "navasan": "abshodeh"}),
    AssetDef("coin_emami", GOLD, "سکه امامی", "Emami coin", "EMAMI", "عدد",
             {"brsapi": "IR_COIN_EMAMI", "navasan": "sekkeh"}),
    AssetDef("coin_bahar", GOLD, "سکه بهار آزادی", "Bahar Azadi coin", "BAHAR", "عدد",
             {"brsapi": "IR_COIN_BAHAR", "navasan": "bahar"}),
    AssetDef("coin_half", GOLD, "نیم سکه", "Half coin", "HALF", "عدد",
             {"brsapi": "IR_COIN_HALF", "navasan": "nim"}),
    AssetDef("coin_quarter", GOLD, "ربع سکه", "Quarter coin", "QTR", "عدد",
             {"brsapi": "IR_COIN_QUARTER", "navasan": "rob"}),
    AssetDef("coin_gerami", GOLD, "سکه گرمی", "1g coin", "1G", "عدد",
             {"brsapi": "IR_COIN_1G", "navasan": "gerami"}),
    AssetDef("gold_ounce", GOLD, "انس جهانی طلا", "Gold ounce", "XAU", "هر اونس",
             {"brsapi": "XAUUSD", "erapi": "XAU"}),
]

CRYPTO_ASSETS = [
    AssetDef("bitcoin", CRYPTO, "بیت‌کوین", "Bitcoin", "BTC", keys={"coingecko": "bitcoin"}),
    AssetDef("ethereum", CRYPTO, "اتریوم", "Ethereum", "ETH", keys={"coingecko": "ethereum"}),
    AssetDef("tether", CRYPTO, "تتر", "Tether", "USDT", keys={"coingecko": "tether"}),
    AssetDef("bnb", CRYPTO, "بی‌ان‌بی", "BNB", "BNB", keys={"coingecko": "binancecoin"}),
    AssetDef("solana", CRYPTO, "سولانا", "Solana", "SOL", keys={"coingecko": "solana"}),
    AssetDef("xrp", CRYPTO, "ریپل", "XRP", "XRP", keys={"coingecko": "ripple"}),
    AssetDef("toncoin", CRYPTO, "تون‌کوین", "Toncoin", "TON", keys={"coingecko": "the-open-network"}),
    AssetDef("dogecoin", CRYPTO, "دوج‌کوین", "Dogecoin", "DOGE", keys={"coingecko": "dogecoin"}),
    AssetDef("cardano", CRYPTO, "کاردانو", "Cardano", "ADA", keys={"coingecko": "cardano"}),
    AssetDef("tron", CRYPTO, "ترون", "TRON", "TRX", keys={"coingecko": "tron"}),
]

FIAT_ASSETS = [
    AssetDef("usd", FIAT, "دلار آمریکا", "US Dollar", "USD", "us",
             {"brsapi": "USD", "navasan": "usd_sell", "erapi": "USD"}),
    AssetDef("eur", FIAT, "یورو", "Euro", "EUR", "eu",
             {"brsapi": "EUR", "navasan": "eur", "erapi": "EUR"}),
    AssetDef("gbp", FIAT, "پوند انگلیس", "British Pound", "GBP", "gb",
             {"brsapi": "GBP", "navasan": "gbp", "erapi": "GBP"}),
    AssetDef("aed", FIAT, "درهم امارات", "UAE Dirham", "AED", "ae",
             {"brsapi": "AED", "navasan": "aed_sell", "erapi": "AED"}),
    AssetDef("try", FIAT, "لیر ترکیه", "Turkish Lira", "TRY", "tr",
             {"brsapi": "TRY", "navasan": "try", "erapi": "TRY"}),
    AssetDef("cny", FIAT, "یوان چین", "Chinese Yuan", "CNY", "cn",
             {"brsapi": "CNY", "navasan": "cny", "erapi": "CNY"}),
    AssetDef("cad", FIAT, "دلار کانادا", "Canadian Dollar", "CAD", "ca",
             {"brsapi": "CAD", "navasan": "cad", "erapi": "CAD"}),
    AssetDef("aud", FIAT, "دلار استرالیا", "Australian Dollar", "AUD", "au",
             {"brsapi": "AUD", "navasan": "aud", "erapi": "AUD"}),
    AssetDef("chf", FIAT, "فرانک سوئیس", "Swiss Franc", "CHF", "ch",
             {"brsapi": "CHF", "navasan": "chf", "erapi": "CHF"}),
    AssetDef("jpy", FIAT, "ین ژاپن", "Japanese Yen", "JPY", "jp",
             {"brsapi": "JPY", "erapi": "JPY"}),
    AssetDef("sar", FIAT, "ریال عربستان", "Saudi Riyal", "SAR", "sa",
             {"brsapi": "SAR", "navasan": "sar", "erapi": "SAR"}),
    AssetDef("rub", FIAT, "روبل روسیه", "Russian Ruble", "RUB", "ru",
             {"brsapi": "RUB", "navasan": "rub", "erapi": "RUB"}),
]

ALL_ASSETS = GOLD_ASSETS + CRYPTO_ASSETS + FIAT_ASSETS
BY_SLUG = {a.slug: a for a in ALL_ASSETS}


def provider_map(provider: str) -> dict[str, str]:
    """Return ``{provider_symbol: slug}`` for one provider."""
    return {a.keys[provider]: a.slug for a in ALL_ASSETS if provider in a.keys}
