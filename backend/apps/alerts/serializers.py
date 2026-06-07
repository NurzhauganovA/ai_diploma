from rest_framework import serializers
from .models import AlertRule, Notification
from apps.articles.serializers import ArticleListSerializer


class AlertRuleSerializer(serializers.ModelSerializer):
    condition_type_display = serializers.CharField(source="get_condition_type_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)

    class Meta:
        model = AlertRule
        fields = "__all__"
        read_only_fields = ["id", "notifications_count", "last_triggered_at", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    article = ArticleListSerializer(read_only=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "rule_name", "article", "status", "channel", "message", "is_read", "sent_at"]
        read_only_fields = ["id", "sent_at"]
