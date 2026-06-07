from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import AlertRule, Notification
from .serializers import AlertRuleSerializer, NotificationSerializer


class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # return all rules as list

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        return Response({"is_active": rule.is_active})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.select_related("rule", "article", "article__source").all()

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save()
        return Response({"is_read": True})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        Notification.objects.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({"detail": "Все уведомления прочитаны."})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(is_read=False).count()
        return Response({"count": count})
