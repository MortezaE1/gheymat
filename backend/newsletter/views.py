from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Subscriber
from .serializers import SubscribeSerializer
from .tasks import send_confirmation_email

# The same answer whatever the address's state, so the endpoint
# cannot be used to find out who is subscribed.
SUBSCRIBE_MESSAGE = "لینک تأیید به ایمیل شما فرستاده شد. لطفاً صندوق ورودی (و پوشه‌ی اسپم) را ببینید."


class SubscribeView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "newsletter"

    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        subscriber, created = Subscriber.objects.get_or_create(email=email)
        if created or subscriber.status != Subscriber.ACTIVE:
            if subscriber.status == Subscriber.UNSUBSCRIBED:
                subscriber.status = Subscriber.PENDING
                subscriber.save(update_fields=["status"])
            send_confirmation_email.delay(subscriber.id)

        return Response({"detail": SUBSCRIBE_MESSAGE}, status=status.HTTP_202_ACCEPTED)


def confirm(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if subscriber.status != Subscriber.ACTIVE:
        subscriber.status = Subscriber.ACTIVE
        subscriber.confirmed_at = timezone.now()
        subscriber.unsubscribed_at = None
        subscriber.save(update_fields=["status", "confirmed_at", "unsubscribed_at"])
    return HttpResponseRedirect(f"{settings.SITE_URL}/?newsletter=confirmed")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def unsubscribe(request, token):
    """GET from the link in the email; POST for RFC 8058 one-click unsubscribe."""
    subscriber = get_object_or_404(Subscriber, token=token)
    if subscriber.status != Subscriber.UNSUBSCRIBED:
        subscriber.status = Subscriber.UNSUBSCRIBED
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save(update_fields=["status", "unsubscribed_at"])
    if request.method == "POST":
        return HttpResponse(status=200)
    return HttpResponseRedirect(f"{settings.SITE_URL}/?newsletter=unsubscribed")
