import re

import pytest
from django.core import mail

from newsletter.models import Issue, Subscriber
from newsletter.tasks import send_daily_newsletter
from prices.services import update_prices
from tests.test_prices import providers

pytestmark = pytest.mark.django_db


def subscribe(client, email="Ali@Example.com"):
    return client.post("/api/newsletter/subscribe/", {"email": email}, content_type="application/json")


def test_subscribe_sends_confirmation_and_confirm_activates(client):
    assert subscribe(client).status_code == 202
    subscriber = Subscriber.objects.get(email="ali@example.com")
    assert subscriber.status == Subscriber.PENDING
    assert len(mail.outbox) == 1
    link = re.search(r"http://\S+/confirm/\S+/", mail.outbox[0].body).group(0)
    response = client.get(link.replace("http://localhost:8000", ""))
    assert response.status_code == 302 and "confirmed" in response["Location"]
    subscriber.refresh_from_db()
    assert subscriber.status == Subscriber.ACTIVE


def test_resubscribe_active_sends_nothing_and_same_answer(client):
    Subscriber.objects.create(email="ali@example.com", status=Subscriber.ACTIVE)
    first = subscribe(client)
    assert first.status_code == 202 and len(mail.outbox) == 0


def test_invalid_email_rejected(client):
    assert subscribe(client, "not-an-email").status_code == 400


def test_daily_newsletter_sends_once_per_day():
    update_prices(providers())
    active = Subscriber.objects.create(email="a@example.com", status=Subscriber.ACTIVE)
    Subscriber.objects.create(email="p@example.com", status=Subscriber.PENDING)
    Subscriber.objects.create(email="u@example.com", status=Subscriber.UNSUBSCRIBED)

    send_daily_newsletter()
    assert [m.to for m in mail.outbox] == [["a@example.com"]]
    message = mail.outbox[0]
    html = message.alternatives[0][0]
    assert "طلای ۱۸ عیار" in html and "۷٬۰۰۰٬۰۰۰" in html
    assert message.extra_headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"

    issue = Issue.objects.get()
    assert (issue.recipients, issue.sent, issue.failed) == (1, 1, 0) and issue.finished_at

    send_daily_newsletter()  # beat firing twice must not double-send
    assert len(mail.outbox) == 1

    active.refresh_from_db()
    assert active.last_sent_at is not None


def test_unsubscribe_get_and_one_click_post(client):
    s = Subscriber.objects.create(email="a@example.com", status=Subscriber.ACTIVE)
    assert client.post(f"/api/newsletter/unsubscribe/{s.token}/").status_code == 200
    s.refresh_from_db()
    assert s.status == Subscriber.UNSUBSCRIBED
    assert client.get(f"/api/newsletter/unsubscribe/{s.token}/").status_code == 302
