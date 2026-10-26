from django.contrib import admin

from .models import Asset, PriceHistory


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name_fa", "symbol", "category", "price_toman", "price_usd", "change_24h", "source", "updated_at", "is_active")
    list_filter = ("category", "is_active", "source")
    list_editable = ("is_active",)
    search_fields = ("name_fa", "name_en", "symbol", "slug")


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("asset", "price_toman", "price_usd", "recorded_at")
    list_filter = ("asset__category",)
    date_hierarchy = "recorded_at"
