"""Persian number formatting for templates (emails)."""

from decimal import Decimal

from django import template

from prices.formatting import fa_digits, format_change, format_toman, format_usd

register = template.Library()

register.filter("fa_digits", fa_digits)
register.filter("toman", format_toman)
register.filter("usd", format_usd)
register.filter("change", format_change)


@register.filter
def is_up(value) -> bool:
    return value is not None and Decimal(str(value)) > 0


@register.filter
def is_down(value) -> bool:
    return value is not None and Decimal(str(value)) < 0
