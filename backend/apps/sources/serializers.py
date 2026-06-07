from rest_framework import serializers
from .models import Source


class SourceSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(source="get_source_type_display", read_only=True)
    last_crawled_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Source
        fields = "__all__"
        read_only_fields = ["id", "articles_count", "last_crawled_at", "created_at", "updated_at"]
