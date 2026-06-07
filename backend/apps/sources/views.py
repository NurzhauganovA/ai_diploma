from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Source
from .serializers import SourceSerializer
from apps.articles.tasks import crawl_source


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["source_type", "is_active"]
    pagination_class = None  # return all sources as list

    @action(detail=True, methods=["post"])
    def crawl_now(self, request, pk=None):
        source = self.get_object()
        if not source.is_active:
            return Response({"detail": "Источник неактивен."}, status=status.HTTP_400_BAD_REQUEST)
        crawl_source.delay(source.id)
        return Response({"detail": f"Обход источника '{source.name}' запущен."})

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        source = self.get_object()
        source.is_active = not source.is_active
        source.save()
        return Response({"is_active": source.is_active})
