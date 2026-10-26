from django.urls import path

from . import views

urlpatterns = [
    path("prices/", views.PriceListView.as_view(), name="price-list"),
    path("prices/<slug:slug>/history/", views.PriceHistoryView.as_view(), name="price-history"),
]
