from django.db import models
from apps.sources.models import Source


class Article(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает обработки"),
        (STATUS_PROCESSED, "Обработана"),
        (STATUS_FAILED, "Ошибка"),
    ]

    URGENCY_LOW = "low"
    URGENCY_MEDIUM = "medium"
    URGENCY_HIGH = "high"
    URGENCY_CRITICAL = "critical"

    URGENCY_CHOICES = [
        (URGENCY_LOW, "Низкая"),
        (URGENCY_MEDIUM, "Средняя"),
        (URGENCY_HIGH, "Высокая"),
        (URGENCY_CRITICAL, "Критическая"),
    ]

    # Content
    url = models.URLField(max_length=1000, unique=True)
    title = models.CharField(max_length=500)
    content = models.TextField(blank=True)
    summary = models.TextField(blank=True, max_length=500)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles")
    author = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    language = models.CharField(max_length=10, default="ru")

    # ML Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    fake_score = models.FloatField(null=True, blank=True, help_text="0=реальное, 1=фейк")
    sentiment = models.CharField(max_length=20, blank=True, help_text="positive/neutral/negative")
    sentiment_score = models.FloatField(null=True, blank=True)
    toxicity_score = models.FloatField(null=True, blank=True)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default=URGENCY_LOW)
    topic = models.CharField(max_length=100, blank=True)
    entities = models.JSONField(default=list, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    shap_data = models.JSONField(default=dict, blank=True)

    # Meta
    is_verified = models.BooleanField(null=True, blank=True, help_text="null=не проверено, True=верифицировано, False=ложная тревога")
    is_about_company = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ["-collected_at"]

    def __str__(self):
        return self.title[:80]

    @property
    def threat_level(self):
        if self.fake_score is None:
            return "unknown"
        if self.fake_score >= 0.75:
            return "high"
        if self.fake_score >= 0.5:
            return "medium"
        return "low"
