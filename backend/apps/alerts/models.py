from django.db import models
from apps.users.models import User


class AlertRule(models.Model):
    CONDITION_FAKE = "fake_score"
    CONDITION_SENTIMENT = "sentiment"
    CONDITION_TOXICITY = "toxicity"
    CONDITION_KEYWORD = "keyword"
    CONDITION_URGENCY = "urgency"

    CONDITION_CHOICES = [
        (CONDITION_FAKE, "Fake Score"),
        (CONDITION_SENTIMENT, "Тональность"),
        (CONDITION_TOXICITY, "Токсичность"),
        (CONDITION_KEYWORD, "Ключевое слово"),
        (CONDITION_URGENCY, "Уровень угрозы"),
    ]

    CHANNEL_EMAIL = "email"
    CHANNEL_TELEGRAM = "telegram"
    CHANNEL_IN_APP = "in_app"

    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_TELEGRAM, "Telegram"),
        (CHANNEL_IN_APP, "В приложении"),
    ]

    name = models.CharField(max_length=200, verbose_name="Название правила")
    condition_type = models.CharField(max_length=30, choices=CONDITION_CHOICES)
    threshold = models.FloatField(null=True, blank=True, help_text="Порог для числовых условий")
    keyword = models.CharField(max_length=200, blank=True, help_text="Ключевое слово для поиска")
    urgency_level = models.CharField(max_length=20, blank=True, help_text="high/critical для urgency условия")
    sentiment_value = models.CharField(max_length=20, blank=True, help_text="negative/positive/neutral")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default=CHANNEL_IN_APP)
    recipients = models.ManyToManyField(User, blank=True, related_name="alert_rules")
    telegram_chat_id = models.CharField(max_length=100, blank=True)
    email_recipients = models.TextField(blank=True, help_text="Email-адреса через запятую")
    is_active = models.BooleanField(default=True)
    notifications_count = models.IntegerField(default=0)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Правило алерта"
        verbose_name_plural = "Правила алертов"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Notification(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает"),
        (STATUS_SENT, "Отправлено"),
        (STATUS_FAILED, "Ошибка"),
    ]

    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="notifications")
    article = models.ForeignKey("articles.Article", on_delete=models.CASCADE, related_name="notifications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    channel = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"[{self.rule.name}] {self.article.title[:50]}"
