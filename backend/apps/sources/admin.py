from django.contrib import admin
from .models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ["name", "source_type", "is_active", "articles_count", "credibility_score", "last_crawled_at"]
    list_filter = ["source_type", "is_active"]
    search_fields = ["name", "url"]
    list_editable = ["is_active", "credibility_score"]
