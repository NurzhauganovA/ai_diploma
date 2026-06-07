from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_ANALYST = "analyst"
    ROLE_PR = "pr_manager"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Администратор"),
        (ROLE_ANALYST, "Аналитик"),
        (ROLE_PR, "PR Менеджер"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ANALYST)
    company_name = models.CharField(max_length=200, blank=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
