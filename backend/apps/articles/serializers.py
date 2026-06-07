from rest_framework import serializers
from .models import Article
from apps.sources.serializers import SourceSerializer


class ArticleListSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True, default="")
    threat_level = serializers.CharField(read_only=True)
    sentiment_display = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "title", "summary", "url", "source_name", "language",
            "fake_score", "sentiment", "sentiment_display", "toxicity_score",
            "urgency", "topic", "status", "threat_level",
            "is_verified", "is_about_company", "published_at", "collected_at",
        ]

    def get_sentiment_display(self, obj):
        mapping = {"positive": "Позитивный", "neutral": "Нейтральный", "negative": "Негативный"}
        return mapping.get(obj.sentiment, obj.sentiment)


class ArticleDetailSerializer(serializers.ModelSerializer):
    source = SourceSerializer(read_only=True)
    threat_level = serializers.CharField(read_only=True)

    class Meta:
        model = Article
        fields = "__all__"


class ArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["url", "title", "content", "source", "author", "published_at", "image_url"]
