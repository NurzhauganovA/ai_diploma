"""
Telegram Bot для FakeGuard.

Запуск: python manage.py run_telegram_bot
Docker: отдельный сервис 'telegram-bot'

Команды бота:
  /start   — приветствие
  /help    — список команд
  /stats   — статистика системы
  /latest  — последние 5 статей с высоким риском
  /alerts  — непрочитанные уведомления
  /report  — краткий дневной отчёт
  /company — название мониторируемой компании
"""
import time
import logging
import os
import django

logger = logging.getLogger(__name__)

TG_API = "https://api.telegram.org/bot{token}/{method}"


def _api(token: str, method: str, **kwargs) -> dict:
    import requests
    url = TG_API.format(token=token, method=method)
    try:
        resp = requests.post(url, json=kwargs, timeout=10)
        return resp.json()
    except Exception as e:
        logger.error(f"Telegram API error: {e}")
        return {}


def send(token: str, chat_id, text: str, parse_mode="HTML"):
    return _api(token, "sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode)


def get_updates(token: str, offset: int = 0) -> list:
    import requests
    url = TG_API.format(token=token, method="getUpdates")
    try:
        resp = requests.get(
            url,
            params={"offset": offset, "timeout": 25, "allowed_updates": ["message"]},
            timeout=30,
        )
        return resp.json().get("result", [])
    except Exception:
        return []


# ── Command handlers ──────────────────────────────────────────────

def cmd_start(token, chat_id, username=""):
    text = (
        "👋 <b>FakeGuard Bot</b>\n\n"
        "Я слежу за фейками и негативом в новостях.\n\n"
        "Доступные команды:\n"
        "/stats — статистика\n"
        "/latest — последние опасные статьи\n"
        "/alerts — непрочитанные уведомления\n"
        "/report — дневной отчёт\n"
        "/company — мониторируемая компания\n"
        "/help — помощь"
    )
    send(token, chat_id, text)


def cmd_stats(token, chat_id):
    try:
        from apps.articles.models import Article
        from apps.alerts.models import Notification
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg
        from django.conf import settings

        now = timezone.now()
        total = Article.objects.count()
        today = Article.objects.filter(collected_at__gte=now - timedelta(hours=24)).count()
        fakes = Article.objects.filter(fake_score__gte=0.6).count()
        negative = Article.objects.filter(sentiment="negative").count()
        critical = Article.objects.filter(urgency="critical").count()
        unread = Notification.objects.filter(is_read=False).count()
        avg_fake = Article.objects.filter(fake_score__isnull=False).aggregate(v=Avg("fake_score"))["v"] or 0
        reputation = max(0, min(100, int((1 - avg_fake) * 100)))
        company = getattr(settings, "MONITORED_COMPANY", "Неизвестно")

        rep_emoji = "🟢" if reputation >= 70 else "🟡" if reputation >= 45 else "🔴"

        text = (
            f"📊 <b>Статистика FakeGuard</b>\n"
            f"🏢 Компания: <b>{company}</b>\n\n"
            f"📰 Всего статей: <b>{total}</b>\n"
            f"🆕 За 24 часа: <b>{today}</b>\n"
            f"🚨 Фейков (≥60%): <b>{fakes}</b>\n"
            f"😠 Негативных: <b>{negative}</b>\n"
            f"💣 Критических: <b>{critical}</b>\n"
            f"🔔 Непрочитанных алертов: <b>{unread}</b>\n\n"
            f"{rep_emoji} Индекс репутации: <b>{reputation}/100</b>"
        )
    except Exception as e:
        text = f"❌ Ошибка при получении статистики: {e}"
    send(token, chat_id, text)


def cmd_latest(token, chat_id):
    try:
        from apps.articles.models import Article

        articles = Article.objects.filter(
            fake_score__isnull=False
        ).order_by("-fake_score", "-collected_at")[:5]

        if not articles:
            send(token, chat_id, "📭 Статей с анализом пока нет.")
            return

        lines = ["🚨 <b>Топ-5 статей по риску фейка:</b>\n"]
        for i, a in enumerate(articles, 1):
            fake = f"{(a.fake_score or 0):.0%}"
            sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😠"}.get(a.sentiment, "❓")
            urgency_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(a.urgency, "⚪")
            title_short = a.title[:80] + ("..." if len(a.title) > 80 else "")
            lines.append(
                f"{i}. {urgency_emoji} <b>{title_short}</b>\n"
                f"   🎭 Фейк: {fake} | {sentiment_emoji} {a.sentiment}\n"
                f"   🔗 <a href='{a.url}'>Читать</a>"
            )

        send(token, chat_id, "\n".join(lines))
    except Exception as e:
        send(token, chat_id, f"❌ Ошибка: {e}")


def cmd_alerts(token, chat_id):
    try:
        from apps.alerts.models import Notification

        notifications = Notification.objects.filter(
            is_read=False
        ).select_related("rule", "article").order_by("-sent_at")[:5]

        if not notifications:
            send(token, chat_id, "✅ Непрочитанных уведомлений нет.")
            return

        lines = [f"🔔 <b>Непрочитанных уведомлений: {notifications.count()}</b>\n"]
        for n in notifications:
            title = n.article.title[:60] + ("..." if len(n.article.title) > 60 else "")
            lines.append(f"• <b>{n.rule.name}</b>\n  {title}")

        send(token, chat_id, "\n".join(lines))
    except Exception as e:
        send(token, chat_id, f"❌ Ошибка: {e}")


def cmd_report(token, chat_id):
    try:
        from apps.articles.models import Article
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg, Count
        from django.conf import settings

        now = timezone.now()
        since = now - timedelta(hours=24)
        company = getattr(settings, "MONITORED_COMPANY", "")

        articles = Article.objects.filter(collected_at__gte=since)
        total = articles.count()

        if total == 0:
            send(token, chat_id, "📭 За последние 24 часа новых статей нет.")
            return

        fakes = articles.filter(fake_score__gte=0.6).count()
        neg = articles.filter(sentiment="negative").count()
        pos = articles.filter(sentiment="positive").count()
        critical = articles.filter(urgency__in=["high", "critical"]).count()
        avg_fake = articles.filter(fake_score__isnull=False).aggregate(v=Avg("fake_score"))["v"] or 0

        top_fake = articles.filter(fake_score__isnull=False).order_by("-fake_score").first()

        text = (
            f"📋 <b>Дневной отчёт FakeGuard</b>\n"
            f"🏢 Компания: <b>{company}</b>\n"
            f"🗓 {now.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📰 Новых статей: <b>{total}</b>\n"
            f"🚨 Фейков: <b>{fakes}</b> ({fakes/total:.0%})\n"
            f"😠 Негативных: <b>{neg}</b>\n"
            f"😊 Позитивных: <b>{pos}</b>\n"
            f"⚠️ Угрозы (high+critical): <b>{critical}</b>\n"
            f"📈 Средний fake score: <b>{avg_fake:.1%}</b>\n"
        )

        if top_fake:
            text += (
                f"\n🔴 <b>Наиболее опасная статья:</b>\n"
                f"{top_fake.title[:100]}\n"
                f"Fake: {(top_fake.fake_score or 0):.0%} | "
                f"<a href='{top_fake.url}'>Читать</a>"
            )

        send(token, chat_id, text)
    except Exception as e:
        send(token, chat_id, f"❌ Ошибка: {e}")


def cmd_company(token, chat_id):
    try:
        from apps.sources.models import Source
        from django.conf import settings

        company = getattr(settings, "MONITORED_COMPANY", "Не настроено")
        sources = Source.objects.filter(is_active=True).count()
        total_sources = Source.objects.count()

        text = (
            f"🏢 <b>Мониторинг компании</b>\n\n"
            f"Компания: <b>{company}</b>\n"
            f"Активных источников: <b>{sources}</b> из {total_sources}\n\n"
            f"Изменить компанию можно в файле <code>.env</code>:\n"
            f"<code>MONITORED_COMPANY=Яндекс</code>"
        )
        send(token, chat_id, text)
    except Exception as e:
        send(token, chat_id, f"❌ Ошибка: {e}")


def cmd_help(token, chat_id):
    text = (
        "📖 <b>Команды FakeGuard Bot</b>\n\n"
        "/start — приветствие\n"
        "/stats — полная статистика системы\n"
        "/latest — топ-5 статей по риску фейка\n"
        "/alerts — непрочитанные уведомления\n"
        "/report — дневной отчёт за 24 часа\n"
        "/company — мониторируемая компания\n"
        "/help — эта справка\n\n"
        "🤖 Бот автоматически присылает уведомления\n"
        "   когда срабатывают правила алертов."
    )
    send(token, chat_id, text)


COMMANDS = {
    "/start": cmd_start,
    "/help": cmd_help,
    "/stats": cmd_stats,
    "/latest": cmd_latest,
    "/alerts": cmd_alerts,
    "/report": cmd_report,
    "/company": cmd_company,
}


def handle_update(token: str, update: dict):
    message = update.get("message", {})
    if not message:
        return
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()
    username = message.get("from", {}).get("username", "")

    if not chat_id or not text.startswith("/"):
        return

    # Handle /command@botname format
    cmd = text.split("@")[0].split(" ")[0].lower()

    handler = COMMANDS.get(cmd)
    if handler:
        logger.info(f"Command {cmd} from {username} ({chat_id})")
        if cmd == "/start":
            handler(token, chat_id, username)
        else:
            handler(token, chat_id)
    else:
        send(token, chat_id, f"❓ Неизвестная команда: {cmd}\nИспользуй /help")


class Command:
    help = "Запустить Telegram Bot (long polling)"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        from django.conf import settings

        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not token:
            self.stdout.write("⚠️  TELEGRAM_BOT_TOKEN не задан. Бот не запущен.")
            self.stdout.write("   Добавьте токен в .env и docker-compose.yml")
            return

        self.stdout.write(f"🤖 Telegram Bot запущен (long polling)...")
        self.stdout.write("   Остановить: Ctrl+C\n")

        offset = 0
        while True:
            try:
                updates = get_updates(token, offset)
                for update in updates:
                    handle_update(token, update)
                    offset = update["update_id"] + 1
            except KeyboardInterrupt:
                self.stdout.write("\n⛔ Бот остановлен")
                break
            except Exception as e:
                logger.error(f"Bot loop error: {e}")
                time.sleep(5)


# Allow running as a management command via Django
from django.core.management.base import BaseCommand as _BaseCommand


class Command(_BaseCommand):
    help = "Запустить Telegram Bot (long polling)"

    def handle(self, *args, **options):
        # Configure Django if running standalone
        if not os.environ.get("DJANGO_SETTINGS_MODULE"):
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
            django.setup()

        from django.conf import settings

        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not token:
            self.stdout.write(self.style.WARNING(
                "⚠️  TELEGRAM_BOT_TOKEN не задан.\n"
                "   Добавь токен в .env:\n"
                "   TELEGRAM_BOT_TOKEN=1234567890:ABC...\n"
                "   И в docker-compose.yml → TELEGRAM_BOT_TOKEN"
            ))
            return

        self.stdout.write(self.style.SUCCESS("🤖 Telegram Bot запущен (long polling)"))
        self.stdout.write("   Команды: /start /stats /latest /alerts /report /company /help")
        self.stdout.write("   Остановить: Ctrl+C\n")

        offset = 0
        while True:
            try:
                updates = get_updates(token, offset)
                for update in updates:
                    handle_update(token, update)
                    offset = update["update_id"] + 1
            except KeyboardInterrupt:
                self.stdout.write("\n⛔ Бот остановлен")
                break
            except Exception as e:
                logger.error(f"Bot loop error: {e}")
                time.sleep(5)
