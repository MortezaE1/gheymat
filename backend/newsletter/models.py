import uuid

from django.db import models


class Subscriber(models.Model):
    PENDING = "pending"
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    STATUS_CHOICES = [
        (PENDING, "در انتظار تأیید"),
        (ACTIVE, "فعال"),
        (UNSUBSCRIBED, "لغو شده"),
    ]

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    # One secret per subscriber, used in both the confirm and unsubscribe links.
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class Issue(models.Model):
    """One daily newsletter. The unique date stops a double send if beat fires twice."""

    date = models.DateField(unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    recipients = models.PositiveIntegerField(default=0)
    sent = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"خبرنامه {self.date}"
