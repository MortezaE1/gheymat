from django.contrib import admin, messages

from .emails import send_daily_email
from .models import Issue, Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "created_at", "confirmed_at", "last_sent_at")
    list_filter = ("status",)
    search_fields = ("email",)
    readonly_fields = ("token", "created_at", "confirmed_at", "unsubscribed_at", "last_sent_at")
    actions = ["send_preview"]

    @admin.action(description="ارسال نمونه‌ی خبرنامه‌ی امروز به این افراد")
    def send_preview(self, request, queryset):
        sent = sum(send_daily_email(s) for s in queryset)
        self.message_user(request, f"{sent} ایمیل فرستاده شد.", messages.SUCCESS)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("date", "recipients", "sent", "failed", "started_at", "finished_at")
