from django.urls import path

from . import views

urlpatterns = [
    path("subscribe/", views.SubscribeView.as_view(), name="newsletter-subscribe"),
    path("confirm/<uuid:token>/", views.confirm, name="newsletter-confirm"),
    path("unsubscribe/<uuid:token>/", views.unsubscribe, name="newsletter-unsubscribe"),
]
