from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "source", "status", "urgency", "sentiment", "fake_score", "collected_at"]
    list_filter = ["status", "urgency", "sentiment", "language"]
    search_fields = ["title", "content", "url"]
    readonly_fields = ["collected_at", "processed_at", "shap_data", "entities", "keywords"]
    list_per_page = 30
