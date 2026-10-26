"""Rendering and sending of the newsletter emails."""

from __future__ import annotations

import logging

import jdatetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from prices.formatting import fa_digits
from prices.views import build_price_payload

from .models import Subscriber

logger = logging.getLogger(__name__)

HIGHLIGHTS = ["usd", "gold_18k", "coin_emami", "bitcoin"]
SECTIONS = [
    ("gold", "طلا و سکه"),
    ("fiat", "ارزهای رسمی"),
    ("crypto", "ارزهای دیجیتال"),
]


def persian_date(dt=None) -> str:
    dt = timezone.localtime(dt or timezone.now())
    j = jdatetime.datetime.fromgregorian(datetime=dt, locale="fa_IR")
    return fa_digits(f"{j.strftime('%A')} {j.day} {j.strftime('%B')} {j.year}")


def build_context(prices: dict | None = None) -> dict:
    """Everything the daily email needs except the per-subscriber links."""
    prices = prices or build_price_payload()
    by_slug = {row["slug"]: row for rows in prices["categories"].values() for row in rows}
    return {
        "date_fa": persian_date(),
        "time_fa": fa_digits(timezone.localtime().strftime("%H:%M")),
        "highlights": [by_slug[s] for s in HIGHLIGHTS if s in by_slug],
        "sections": [
            {"key": key, "title": title, "rows": prices["categories"].get(key, [])}
            for key, title in SECTIONS
        ],
        "is_demo": prices.get("is_demo", False),
        "site_url": settings.SITE_URL,
    }


def _unsubscribe_url(subscriber: Subscriber) -> str:
    return settings.API_PUBLIC_URL + reverse("newsletter-unsubscribe", args=[subscriber.token])


def send_daily_email(subscriber: Subscriber, context: dict | None = None, connection=None) -> int:
    context = {**(context or build_context()), "unsubscribe_url": _unsubscribe_url(subscriber)}
    subject = f"قیمت‌های امروز | {context['date_fa']}"
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string("newsletter/daily.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
        connection=connection,
        headers={
            "List-Unsubscribe": f"<{context['unsubscribe_url']}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    )
    message.attach_alternative(render_to_string("newsletter/daily.html", context), "text/html")
    return message.send()


def send_confirmation(subscriber: Subscriber) -> int:
    context = {
        "confirm_url": settings.API_PUBLIC_URL + reverse("newsletter-confirm", args=[subscriber.token]),
        "site_url": settings.SITE_URL,
    }
    message = EmailMultiAlternatives(
        subject="تأیید عضویت در خبرنامه‌ی قیمت",
        body=render_to_string("newsletter/confirm.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    message.attach_alternative(render_to_string("newsletter/confirm.html", context), "text/html")
    return message.send()
