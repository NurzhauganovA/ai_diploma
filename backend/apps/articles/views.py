from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Article
from .serializers import ArticleListSerializer, ArticleDetailSerializer, ArticleCreateSerializer
from .filters import ArticleFilter
from .tasks import analyze_article


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("source").all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ["title", "content", "summary", "topic"]
    ordering_fields = ["collected_at", "fake_score", "urgency", "published_at"]
    ordering = ["-collected_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleListSerializer
        if self.action == "create":
            return ArticleCreateSerializer
        return ArticleDetailSerializer

    def perform_create(self, serializer):
        article = serializer.save(status=Article.STATUS_PENDING)
        analyze_article.delay(article.id)

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        article = self.get_object()
        is_real = request.data.get("is_real", True)
        article.is_verified = is_real
        article.save()
        return Response({"detail": "Статья верифицирована.", "is_verified": article.is_verified})

    @action(detail=True, methods=["post"])
    def reanalyze(self, request, pk=None):
        article = self.get_object()
        article.status = Article.STATUS_PENDING
        article.save()
        analyze_article.delay(article.id)
        return Response({"detail": "Повторный анализ запущен."})

    @action(detail=False, methods=["post"])
    def add_url(self, request):
        url = request.data.get("url", "").strip()
        if not url:
            return Response({"detail": "URL обязателен."}, status=status.HTTP_400_BAD_REQUEST)

        if Article.objects.filter(url=url).exists():
            article = Article.objects.get(url=url)
            return Response(ArticleListSerializer(article).data)

        from apps.articles.tasks import fetch_and_analyze_url
        task = fetch_and_analyze_url.delay(url)
        return Response({"detail": "URL добавлен в очередь анализа.", "task_id": task.id}, status=status.HTTP_202_ACCEPTED)
