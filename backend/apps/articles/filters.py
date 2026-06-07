import django_filters
from .models import Article


class ArticleFilter(django_filters.FilterSet):
    sentiment = django_filters.CharFilter(lookup_expr="exact")
    urgency = django_filters.CharFilter(lookup_expr="exact")
    status = django_filters.CharFilter(lookup_expr="exact")
    source = django_filters.NumberFilter(field_name="source__id")
    language = django_filters.CharFilter(lookup_expr="exact")
    is_verified = django_filters.BooleanFilter()
    fake_score_min = django_filters.NumberFilter(field_name="fake_score", lookup_expr="gte")
    fake_score_max = django_filters.NumberFilter(field_name="fake_score", lookup_expr="lte")
    collected_after = django_filters.DateTimeFilter(field_name="collected_at", lookup_expr="gte")
    collected_before = django_filters.DateTimeFilter(field_name="collected_at", lookup_expr="lte")
    topic = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Article
        fields = ["sentiment", "urgency", "status", "source", "language",
                  "is_verified", "fake_score_min", "fake_score_max", "topic"]
