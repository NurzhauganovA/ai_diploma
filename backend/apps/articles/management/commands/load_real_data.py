"""
Команда для загрузки реальных данных о компании из публичных RSS-лент.
Использует Google News RSS + ведущие российские СМИ.

Использование:
    python manage.py load_real_data --company "Яндекс" --limit 50
    python manage.py load_real_data --company "Сбербанк" --limit 30
    python manage.py load_real_data --company "Газпром" --limit 20
"""
from django.core.management.base import BaseCommand


REAL_SOURCES = [
    # Google News RSS — статьи по ключевому слову (самые актуальные)
    {
        "name_template": "Google News: {company}",
        "url_template": "https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru",
        "source_type": "rss",
        "credibility_score": 0.75,
    },
    {
        "name_template": "Google News EN: {company}",
        "url_template": "https://news.google.com/rss/search?q={query_en}&hl=en&gl=RU&ceid=RU:en",
        "source_type": "rss",
        "credibility_score": 0.75,
    },
    # Ведущие российские СМИ
    {
        "name": "РИА Новости",
        "url": "https://ria.ru/export/rss2/index.xml",
        "source_type": "rss",
        "credibility_score": 0.82,
    },
    {
        "name": "РБК",
        "url": "https://rbc.ru/rss/news",
        "source_type": "rss",
        "credibility_score": 0.85,
    },
    {
        "name": "Коммерсантъ",
        "url": "https://www.kommersant.ru/RSS/corp.xml",
        "source_type": "rss",
        "credibility_score": 0.90,
    },
    {
        "name": "Ведомости",
        "url": "https://www.vedomosti.ru/rss/news",
        "source_type": "rss",
        "credibility_score": 0.90,
    },
    {
        "name": "Habr (технологии)",
        "url": "https://habr.com/ru/rss/best/daily/",
        "source_type": "rss",
        "credibility_score": 0.78,
    },
    {
        "name": "TechCrunch (EN)",
        "url": "https://techcrunch.com/feed/",
        "source_type": "rss",
        "credibility_score": 0.88,
    },
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "source_type": "rss",
        "credibility_score": 0.92,
    },
]

# Известные компании и их переводы/алиасы для поиска
COMPANY_ALIASES = {
    "яндекс": {"ru": "Яндекс", "en": "Yandex", "display": "Яндекс"},
    "yandex": {"ru": "Яндекс", "en": "Yandex", "display": "Яндекс"},
    "сбербанк": {"ru": "Сбербанк", "en": "Sberbank", "display": "Сбербанк"},
    "sberbank": {"ru": "Сбербанк", "en": "Sberbank", "display": "Сбербанк"},
    "газпром": {"ru": "Газпром", "en": "Gazprom", "display": "Газпром"},
    "gazprom": {"ru": "Газпром", "en": "Gazprom", "display": "Газпром"},
    "лукойл": {"ru": "Лукойл", "en": "Lukoil", "display": "Лукойл"},
    "lukoil": {"ru": "Лукойл", "en": "Lukoil", "display": "Лукойл"},
    "мтс": {"ru": "МТС", "en": "MTS", "display": "МТС"},
    "mts": {"ru": "МТС", "en": "MTS", "display": "МТС"},
    "вконтакте": {"ru": "ВКонтакте", "en": "VKontakte", "display": "ВКонтакте"},
    "vk": {"ru": "ВКонтакте", "en": "VK VKontakte", "display": "VK"},
    "тинькофф": {"ru": "Тинькофф", "en": "Tinkoff", "display": "Тинькофф"},
    "tinkoff": {"ru": "Тинькофф", "en": "Tinkoff", "display": "Тинькофф"},
    "apple": {"ru": "Apple", "en": "Apple", "display": "Apple"},
    "google": {"ru": "Google", "en": "Google", "display": "Google"},
    "microsoft": {"ru": "Microsoft", "en": "Microsoft", "display": "Microsoft"},
    "tesla": {"ru": "Tesla", "en": "Tesla", "display": "Tesla"},
    "samsung": {"ru": "Samsung", "en": "Samsung", "display": "Samsung"},
    "озон": {"ru": "Ozon", "en": "Ozon", "display": "Ozon"},
    "ozon": {"ru": "Ozon", "en": "Ozon", "display": "Ozon"},
    "wildberries": {"ru": "Wildberries", "en": "Wildberries", "display": "Wildberries"},
}


class Command(BaseCommand):
    help = "Загрузить реальные новости о компании из публичных RSS-лент"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            default="Яндекс",
            help="Название компании для мониторинга (по умолчанию: Яндекс)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Максимальное количество статей для загрузки",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить старые демо-статьи перед загрузкой",
        )

    def handle(self, *args, **options):
        from apps.sources.models import Source
        from apps.articles.models import Article
        from apps.articles.tasks import analyze_article
        from ml.crawler import crawl_rss

        company_input = options["company"].lower().strip()
        limit = options["limit"]

        # Определяем алиасы компании
        aliases = COMPANY_ALIASES.get(company_input, {
            "ru": options["company"],
            "en": options["company"],
            "display": options["company"],
        })

        company_ru = aliases["ru"]
        company_en = aliases["en"]
        company_display = aliases["display"]

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"  Загрузка реальных данных: {company_display}")
        self.stdout.write(f"{'='*50}\n")

        # Очистка старых демо данных если нужно
        if options["clear"]:
            fake_urls = [f"https://example.com/article/{i}" for i in range(1, 20)]
            deleted = Article.objects.filter(url__in=fake_urls).delete()
            self.stdout.write(f"🗑️  Удалено демо-статей: {deleted[0]}")

        # Создаём/обновляем источники
        created_sources = []
        for s_config in REAL_SOURCES:
            if "url_template" in s_config:
                # Динамический источник по компании
                import urllib.parse
                name = s_config["name_template"].format(company=company_display)
                if "{query_en}" in s_config["url_template"]:
                    url = s_config["url_template"].format(
                        query=urllib.parse.quote(company_ru),
                        query_en=urllib.parse.quote(company_en),
                    )
                else:
                    url = s_config["url_template"].format(
                        query=urllib.parse.quote(company_ru),
                        query_en=urllib.parse.quote(company_en),
                    )
            else:
                name = s_config["name"]
                url = s_config["url"]

            source, created = Source.objects.get_or_create(
                url=url,
                defaults={
                    "name": name,
                    "source_type": s_config["source_type"],
                    "credibility_score": s_config["credibility_score"],
                    "is_active": True,
                    "crawl_interval": 1800,
                },
            )
            created_sources.append(source)
            status = "создан" if created else "уже существует"
            self.stdout.write(f"  📡 {source.name} — {status}")

        self.stdout.write(f"\n✅ Источников настроено: {len(created_sources)}\n")

        # Собираем статьи из всех источников
        total_created = 0
        per_source = max(5, limit // len(created_sources))

        for source in created_sources:
            self.stdout.write(f"🔄 Обходим: {source.name}...")
            try:
                articles_data = crawl_rss(source.url, limit=per_source)

                # Фильтруем по ключевым словам компании (для общих лент)
                is_company_specific = "Google News" in source.name
                if not is_company_specific:
                    articles_data = [
                        a for a in articles_data
                        if company_ru.lower() in (a.get("title", "") + a.get("content", "")).lower()
                        or company_en.lower() in (a.get("title", "") + a.get("content", "")).lower()
                    ]

                source_created = 0
                for data in articles_data:
                    if total_created >= limit:
                        break
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
                                "is_about_company": True,
                            },
                        )
                        if is_new:
                            # Запустить ML анализ асинхронно (или синхронно если нет Celery)
                            try:
                                analyze_article.delay(article.id)
                            except Exception:
                                # Celery недоступен — запустить синхронно
                                from ml.analyzer import full_analyze
                                from django.utils import timezone

                                results = full_analyze(
                                    text=article.content or article.summary or article.title,
                                    title=article.title,
                                    source_credibility=source.credibility_score,
                                )
                                for key, val in results.items():
                                    setattr(article, key, val)
                                article.status = Article.STATUS_PROCESSED
                                article.processed_at = timezone.now()
                                article.save()

                            source_created += 1
                            total_created += 1
                    except Exception as e:
                        pass

                # Обновляем счётчик источника
                from django.utils import timezone
                source.last_crawled_at = timezone.now()
                source.articles_count = source.articles.count()
                source.save()

                self.stdout.write(
                    f"   ✓ Новых статей: {source_created} (найдено: {len(articles_data)})"
                )
            except Exception as e:
                self.stdout.write(f"   ⚠️  Ошибка: {e}")

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(self.style.SUCCESS(f"✅ Загружено реальных статей: {total_created}"))
        self.stdout.write(f"   Компания: {company_display}")
        self.stdout.write(f"   ML-анализ запущен в фоне через Celery")
        self.stdout.write(f"{'='*50}\n")
