import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def analyze_article(self, article_id: int):
    """Run full ML analysis on an article."""
    try:
        from .models import Article
        from ml.analyzer import full_analyze

        article = Article.objects.select_related("source").get(id=article_id)
        source_credibility = article.source.credibility_score if article.source else 0.7

        results = full_analyze(
            text=article.content or article.summary or article.title,
            title=article.title,
            source_credibility=source_credibility,
        )

        article.fake_score = results["fake_score"]
        article.sentiment = results["sentiment"]
        article.sentiment_score = results["sentiment_score"]
        article.toxicity_score = results["toxicity_score"]
        article.urgency = results["urgency"]
        article.topic = results["topic"]
        article.entities = results["entities"]
        article.keywords = results["keywords"]
        article.shap_data = results["shap_data"]
        article.status = Article.STATUS_PROCESSED
        article.processed_at = timezone.now()
        article.save()

        # Check alert rules
        check_alerts.delay(article_id)

        logger.info(f"Article {article_id} analyzed: fake={results['fake_score']:.2f}, sentiment={results['sentiment']}")
        return {"article_id": article_id, "status": "success"}

    except Exception as exc:
        logger.error(f"Analysis failed for article {article_id}: {exc}")
        try:
            from .models import Article
            Article.objects.filter(id=article_id).update(status=Article.STATUS_FAILED)
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)


@shared_task
def crawl_source(source_id: int):
    """Crawl a source and create articles."""
    try:
        from apps.sources.models import Source
        from .models import Article
        from ml.crawler import crawl_rss, scrape_url

        source = Source.objects.get(id=source_id)
        logger.info(f"Crawling source: {source.name} ({source.source_type})")

        articles_data = []
        if source.source_type == "rss":
            articles_data = crawl_rss(source.url)
        elif source.source_type == "web":
            data = scrape_url(source.url)
            if data:
                articles_data = [data]

        created = 0
        for data in articles_data:
            try:
                article, is_new = Article.objects.get_or_create(
                    url=data["url"],
                    defaults={
                        "title": data["title"],
                        "content": data.get("content", ""),
                        "summary": data.get("summary", ""),
                        "author": data.get("author", ""),
                        "image_url": data.get("image_url", ""),
                        "published_at": data.get("published_at"),
                        "language": data.get("language", "ru"),
                        "source": source,
                        "status": Article.STATUS_PENDING,
                    },
                )
                if is_new:
                    created += 1
                    analyze_article.delay(article.id)
            except Exception as e:
                logger.error(f"Article save error: {e}")

        source.last_crawled_at = timezone.now()
        source.articles_count = source.articles.count()
        source.save()

        logger.info(f"Source {source.name}: {created} new articles created")
        return {"source_id": source_id, "created": created}

    except Exception as exc:
        logger.error(f"Crawl failed for source {source_id}: {exc}")
        raise


@shared_task
def crawl_all_active_sources():
    """Celery Beat task: crawl all active sources."""
    from apps.sources.models import Source
    from django.utils import timezone as tz
    from datetime import timedelta

    sources = Source.objects.filter(is_active=True)
    dispatched = 0
    for source in sources:
        should_crawl = (
            source.last_crawled_at is None or
            tz.now() - source.last_crawled_at >= timedelta(seconds=source.crawl_interval)
        )
        if should_crawl:
            crawl_source.delay(source.id)
            dispatched += 1

    logger.info(f"Dispatched crawl tasks for {dispatched} sources")
    return dispatched


@shared_task
def check_alerts(article_id: int):
    """Check alert rules for a newly analyzed article."""
    try:
        from .models import Article
        from apps.alerts.models import AlertRule, Notification
        from apps.alerts.services import evaluate_rule, send_notification

        article = Article.objects.select_related("source").get(id=article_id)
        rules = AlertRule.objects.filter(is_active=True)

        for rule in rules:
            if evaluate_rule(rule, article):
                notif = Notification.objects.create(
                    rule=rule,
                    article=article,
                )
                send_notification.delay(notif.id)
    except Exception as e:
        logger.error(f"Alert check failed for article {article_id}: {e}")


@shared_task(bind=True, max_retries=2)
def fetch_and_analyze_url(self, url: str):
    """Fetch content from URL and analyze it."""
    try:
        from .models import Article
        from ml.crawler import scrape_url

        data = scrape_url(url)
        if not data or not data.get("title"):
            raise ValueError(f"Could not extract content from {url}")

        article, created = Article.objects.get_or_create(
            url=url,
            defaults={
                "title": data["title"],
                "content": data.get("content", ""),
                "summary": data.get("summary", ""),
                "author": data.get("author", ""),
                "image_url": data.get("image_url", ""),
                "status": Article.STATUS_PENDING,
            },
        )

        if created or article.status == Article.STATUS_PENDING:
            analyze_article.delay(article.id)

        return {"article_id": article.id, "created": created}
    except Exception as exc:
        logger.error(f"Fetch URL failed for {url}: {exc}")
        raise self.retry(exc=exc, countdown=10)
