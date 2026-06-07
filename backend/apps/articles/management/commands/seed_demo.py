"""
Management command — начальная настройка системы.
Создаёт admin-пользователя, правила алертов и загружает
реальные новости о выбранной компании.

Использование:
    python manage.py seed_demo                          # Яндекс по умолчанию
    python manage.py seed_demo --company "Сбербанк"
    python manage.py seed_demo --company "Tesla"
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Инициализация системы: admin, алерты, реальные данные"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            default="Яндекс",
            help="Компания для мониторинга (по умолчанию: Яндекс)",
        )

    def handle(self, *args, **options):
        from apps.alerts.models import AlertRule

        company = options["company"]
        self.stdout.write("Инициализация FakeGuard...")

        # 1. Создаём admin-пользователя
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                password="admin123",
                email="admin@fakeguard.app",
                role="admin",
                company_name=company,
            )
            self.stdout.write(self.style.SUCCESS("✓ Создан admin/admin123"))
        else:
            self.stdout.write("  admin уже существует")

        # 2. Создаём правила алертов
        if not AlertRule.objects.exists():
            AlertRule.objects.create(
                name="Критический фейк",
                condition_type="fake_score",
                threshold=0.75,
                channel="in_app",
                is_active=True,
            )
            AlertRule.objects.create(
                name="Негативный контент",
                condition_type="sentiment",
                sentiment_value="negative",
                channel="in_app",
                is_active=True,
            )
            AlertRule.objects.create(
                name="Высокая токсичность",
                condition_type="toxicity",
                threshold=0.6,
                channel="in_app",
                is_active=True,
            )
            AlertRule.objects.create(
                name="Критическая угроза",
                condition_type="urgency",
                urgency_level="critical",
                channel="in_app",
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS("✓ Создано 4 правила алертов"))

        # 3. Загрузка реальных данных о компании
        from django.core.management import call_command
        self.stdout.write(f"\n📰 Загрузка реальных новостей о компании: {company}")
        try:
            call_command("load_real_data", company=company, limit=40)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Не удалось загрузить данные: {e}"))
            self.stdout.write("   Система работает, данные можно загрузить позже через:")
            self.stdout.write(f"   python manage.py load_real_data --company \"{company}\"")

        self.stdout.write(self.style.SUCCESS("\n🎉 FakeGuard готов к работе!"))
        self.stdout.write(f"   Мониторинг компании: {company}")
        self.stdout.write("   Логин: admin / Пароль: admin123")
        self.stdout.write("   API: http://localhost:8000/api/docs/")
