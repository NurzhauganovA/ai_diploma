from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from collections import defaultdict

from apps.articles.models import Article
from apps.sources.models import Source
from apps.alerts.models import Notification


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        total = Article.objects.count()
        new_today = Article.objects.filter(collected_at__gte=last_24h).count()
        high_threat = Article.objects.filter(
            collected_at__gte=last_7d,
            urgency__in=["high", "critical"]
        ).count()
        fake_count = Article.objects.filter(fake_score__gte=0.6).count()
        negative_count = Article.objects.filter(sentiment="negative").count()

        avg_fake = Article.objects.filter(
            fake_score__isnull=False
        ).aggregate(avg=Avg("fake_score"))["avg"] or 0

        unread_alerts = Notification.objects.filter(is_read=False).count()

        # Reputation score (inverse of threat)
        reputation_score = max(0, min(100, int((1 - avg_fake) * 100)))

        return Response({
            "total_articles": total,
            "new_today": new_today,
            "high_threat_week": high_threat,
            "fake_count": fake_count,
            "negative_count": negative_count,
            "avg_fake_score": round(avg_fake, 3),
            "reputation_score": reputation_score,
            "unread_alerts": unread_alerts,
            "monitored_company": getattr(settings, "MONITORED_COMPANY", "Яндекс"),
        })


class TrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 7))
        now = timezone.now()
        start = now - timedelta(days=days)

        articles = Article.objects.filter(
            collected_at__gte=start
        ).values("collected_at", "fake_score", "sentiment", "urgency")

        # Group by day
        daily = defaultdict(lambda: {
            "total": 0, "fake": 0, "negative": 0,
            "positive": 0, "high_threat": 0
        })

        for a in articles:
            day = a["collected_at"].strftime("%Y-%m-%d")
            daily[day]["total"] += 1
            if (a["fake_score"] or 0) >= 0.6:
                daily[day]["fake"] += 1
            if a["sentiment"] == "negative":
                daily[day]["negative"] += 1
            elif a["sentiment"] == "positive":
                daily[day]["positive"] += 1
            if a["urgency"] in ("high", "critical"):
                daily[day]["high_threat"] += 1

        # Fill missing days
        result = []
        for i in range(days):
            day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            d = daily.get(day, {"total": 0, "fake": 0, "negative": 0, "positive": 0, "high_threat": 0})
            result.append({"date": day, **d})

        return Response(result)


class SentimentBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        data = (
            Article.objects
            .filter(collected_at__gte=since, sentiment__in=["positive", "neutral", "negative"])
            .values("sentiment")
            .annotate(count=Count("id"))
        )
        result = {d["sentiment"]: d["count"] for d in data}
        return Response({
            "positive": result.get("positive", 0),
            "neutral": result.get("neutral", 0),
            "negative": result.get("negative", 0),
        })


class TopSourcesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        sources = (
            Source.objects
            .filter(articles__collected_at__gte=since)
            .annotate(
                article_count=Count("articles"),
                fake_avg=Avg("articles__fake_score"),
                negative_count=Count("articles", filter=Q(articles__sentiment="negative")),
            )
            .order_by("-article_count")[:10]
        )

        result = [
            {
                "id": s.id,
                "name": s.name,
                "article_count": s.article_count,
                "fake_avg": round(s.fake_avg or 0, 3),
                "negative_count": s.negative_count,
                "credibility_score": s.credibility_score,
            }
            for s in sources
        ]
        return Response(result)


class TopicsBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        data = (
            Article.objects
            .filter(collected_at__gte=since)
            .exclude(topic="")
            .values("topic")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        return Response(list(data))


class UrgencyBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        data = (
            Article.objects
            .filter(collected_at__gte=since)
            .values("urgency")
            .annotate(count=Count("id"))
        )
        result = {d["urgency"]: d["count"] for d in data}
        return Response({
            "low": result.get("low", 0),
            "medium": result.get("medium", 0),
            "high": result.get("high", 0),
            "critical": result.get("critical", 0),
        })


class ReputationHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        now = timezone.now()
        start = now - timedelta(days=days)

        result = []
        for i in range(days):
            day = start + timedelta(days=i)
            day_end = day + timedelta(days=1)

            articles = Article.objects.filter(
                collected_at__gte=day,
                collected_at__lt=day_end,
                fake_score__isnull=False,
            )
            if articles.exists():
                avg_fake = articles.aggregate(avg=Avg("fake_score"))["avg"] or 0
                reputation = max(0, min(100, int((1 - avg_fake) * 100)))
            else:
                reputation = 70  # default when no data

            result.append({
                "date": day.strftime("%Y-%m-%d"),
                "reputation_score": reputation,
            })

        return Response(result)
