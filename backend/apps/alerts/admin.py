from django.contrib import admin
from .models import AlertRule, Notification


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "condition_type", "channel", "is_active", "notifications_count", "last_triggered_at"]
    list_filter = ["condition_type", "channel", "is_active"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["rule", "article", "status", "is_read", "sent_at"]
    list_filter = ["status", "is_read", "channel"]
    readonly_fields = ["sent_at"]
