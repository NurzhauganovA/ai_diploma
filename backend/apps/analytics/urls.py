from django.urls import path
from .views import (
    DashboardStatsView,
    TrendsView,
    SentimentBreakdownView,
    TopSourcesView,
    TopicsBreakdownView,
    UrgencyBreakdownView,
    ReputationHistoryView,
)

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="analytics-dashboard"),
    path("trends/", TrendsView.as_view(), name="analytics-trends"),
    path("sentiment/", SentimentBreakdownView.as_view(), name="analytics-sentiment"),
    path("sources/", TopSourcesView.as_view(), name="analytics-sources"),
    path("topics/", TopicsBreakdownView.as_view(), name="analytics-topics"),
    path("urgency/", UrgencyBreakdownView.as_view(), name="analytics-urgency"),
    path("reputation/", ReputationHistoryView.as_view(), name="analytics-reputation"),
]
