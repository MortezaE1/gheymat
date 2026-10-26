import logging
from datetime import datetime, time

from celery import shared_task
from django.core.mail import get_connection
from django.db.models import F, Q
from django.utils import timezone

from .models import Issue, Subscriber

logger = logging.getLogger(__name__)

BATCH_SIZE = 200


@shared_task(ignore_result=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_confirmation_email(subscriber_id):
    from .emails import send_confirmation

    subscriber = Subscriber.objects.filter(id=subscriber_id).first()
    if subscriber and subscriber.status == Subscriber.PENDING:
        send_confirmation(subscriber)


@shared_task(ignore_result=True)
def send_daily_newsletter():
    """
    Runs at 10:00 Tehran time (see CELERY_BEAT_SCHEDULE). Safe to run more than
    once a day: subscribers already sent today are skipped.
    """
    from .emails import build_context
    from prices.views import build_price_payload

    now = timezone.localtime()
    start_of_day = timezone.make_aware(datetime.combine(now.date(), time.min))
    issue, _ = Issue.objects.get_or_create(date=now.date())

    ids = list(
        Subscriber.objects.filter(status=Subscriber.ACTIVE)
        .filter(Q(last_sent_at__isnull=True) | Q(last_sent_at__lt=start_of_day))
        .values_list("id", flat=True)
    )
    if not ids:
        logger.info("Newsletter %s: nobody left to send to", issue.date)
        return 0

    Issue.objects.filter(id=issue.id).update(recipients=F("recipients") + len(ids))
    # One price snapshot for the whole issue, so every subscriber gets the same numbers.
    context = build_context(build_price_payload())
    for i in range(0, len(ids), BATCH_SIZE):
        send_newsletter_batch.delay(ids[i:i + BATCH_SIZE], issue.id, context)
    logger.info("Newsletter %s: queued %d recipients", issue.date, len(ids))
    return len(ids)


@shared_task(ignore_result=True)
def send_newsletter_batch(subscriber_ids, issue_id, context):
    from .emails import send_daily_email

    sent = failed = 0
    with get_connection() as connection:
        for subscriber in Subscriber.objects.filter(id__in=subscriber_ids, status=Subscriber.ACTIVE):
            try:
                if send_daily_email(subscriber, context, connection=connection):
                    sent += 1
                    Subscriber.objects.filter(id=subscriber.id).update(last_sent_at=timezone.now())
                else:
                    failed += 1
            except Exception:
                failed += 1
                logger.exception("Newsletter to %s failed", subscriber.email)

    Issue.objects.filter(id=issue_id).update(sent=F("sent") + sent, failed=F("failed") + failed)
    issue = Issue.objects.get(id=issue_id)
    if issue.sent + issue.failed >= issue.recipients and issue.finished_at is None:
        Issue.objects.filter(id=issue_id).update(finished_at=timezone.now())
