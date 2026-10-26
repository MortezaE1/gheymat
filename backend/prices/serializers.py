from rest_framework import serializers

from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    # Floats keep the payload JSON-serialisable for the cache and Celery.
    price_toman = serializers.FloatField(allow_null=True)
    price_usd = serializers.FloatField(allow_null=True)
    change_24h = serializers.FloatField(allow_null=True)
    spark = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            "slug", "category", "name_fa", "name_en", "symbol", "unit",
            "price_toman", "price_usd", "change_24h", "source", "updated_at", "spark",
        ]

    def get_spark(self, obj):
        return self.context.get("sparks", {}).get(obj.id, [])
