from decimal import Decimal

FA_DIGITS = str.maketrans("0123456789,.-", "۰۱۲۳۴۵۶۷۸۹٬٫−")


def fa_digits(value) -> str:
    return str(value).translate(FA_DIGITS)


def format_toman(value) -> str:
    if value is None:
        return "—"
    value = Decimal(str(value))
    if value >= 100:
        return fa_digits(f"{value:,.0f}")
    return fa_digits(f"{value:,.2f}")


def format_usd(value) -> str:
    """USD with precision that suits the magnitude ($112,000 vs $0.000012)."""
    if value is None:
        return "—"
    value = Decimal(str(value))
    if value >= 1000:
        text = f"{value:,.0f}"
    elif value >= 1:
        text = f"{value:,.2f}"
    elif value >= Decimal("0.01"):
        text = f"{value:.4f}"
    else:
        text = f"{value:.8f}".rstrip("0")
    return fa_digits(text)


def format_change(value) -> str:
    if value is None:
        return "—"
    value = Decimal(str(value))
    sign = "+" if value > 0 else ""
    return fa_digits(f"{sign}{value:.2f}") + "٪"
