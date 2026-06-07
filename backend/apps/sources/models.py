from django.db import models


class Source(models.Model):
    TYPE_RSS = "rss"
    TYPE_WEB = "web"
    TYPE_TELEGRAM = "telegram"
    TYPE_MANUAL = "manual"

    TYPE_CHOICES = [
        (TYPE_RSS, "RSS лента"),
        (TYPE_WEB, "Веб-сайт"),
        (TYPE_TELEGRAM, "Telegram"),
        (TYPE_MANUAL, "Ручной ввод"),
    ]

    name = models.CharField(max_length=200, verbose_name="Название")
    url = models.URLField(max_length=500, verbose_name="URL")
    source_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_RSS)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    crawl_interval = models.IntegerField(default=1800, help_text="Интервал обхода в секундах (по умолчанию 30 мин)")
    credibility_score = models.FloatField(default=0.7, help_text="Рейтинг доверия источнику (0–1)")
    articles_count = models.IntegerField(default=0)
    last_crawled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
