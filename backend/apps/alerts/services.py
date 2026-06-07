import logging
from celery import shared_task

logger = logging.getLogger(__name__)


def evaluate_rule(rule, article) -> bool:
    """Check if article triggers the alert rule."""
    try:
        if rule.condition_type == "fake_score":
            return (article.fake_score or 0) >= (rule.threshold or 0.7)

        elif rule.condition_type == "sentiment":
            return article.sentiment == rule.sentiment_value

        elif rule.condition_type == "toxicity":
            return (article.toxicity_score or 0) >= (rule.threshold or 0.6)

        elif rule.condition_type == "keyword":
            if not rule.keyword:
                return False
            text = (article.title + " " + (article.content or "")).lower()
            return rule.keyword.lower() in text

        elif rule.condition_type == "urgency":
            urgency_map = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            article_level = urgency_map.get(article.urgency, 0)
            rule_level = urgency_map.get(rule.urgency_level, 2)
            return article_level >= rule_level

    except Exception as e:
        logger.error(f"Rule evaluation error: {e}")
    return False


@shared_task
def send_notification(notification_id: int):
    """Send notification via configured channel."""
    try:
        from .models import Notification
        from django.conf import settings

        notif = Notification.objects.select_related("rule", "article").get(id=notification_id)
        rule = notif.rule
        article = notif.article

        message = (
            f"🚨 Алерт: {rule.name}\n"
            f"📰 {article.title}\n"
            f"🔗 {article.url}\n"
            f"⚠️ Fake Score: {article.fake_score:.0%}\n"
            f"💬 Тональность: {article.sentiment}\n"
            f"🔴 Угроза: {article.urgency}"
        )
        notif.message = message

        if rule.channel == "telegram":
            # Send to rule-specific chat_id OR global TELEGRAM_CHAT_ID
            chat_id = rule.telegram_chat_id or getattr(settings, "TELEGRAM_CHAT_ID", "")
            _send_telegram(settings.TELEGRAM_BOT_TOKEN, chat_id, message)
        elif rule.channel == "email":
            _send_email(rule.email_recipients, rule.name, message)

        # Also send to global Telegram chat for all high/critical alerts
        global_chat = getattr(settings, "TELEGRAM_CHAT_ID", "")
        if global_chat and rule.channel != "telegram" and getattr(article, "urgency", "") in ("high", "critical"):
            _send_telegram(settings.TELEGRAM_BOT_TOKEN, global_chat, message)

        # Always mark in-app
        notif.status = "sent"
        notif.channel = rule.channel
        notif.save()

        from django.utils import timezone
        rule.notifications_count += 1
        rule.last_triggered_at = timezone.now()
        rule.save()

    except Exception as e:
        logger.error(f"Notification send error: {e}")
        try:
            from .models import Notification
            Notification.objects.filter(id=notification_id).update(status="failed")
        except Exception:
            pass


def _send_telegram(token: str, chat_id: str, message: str):
    """Send Telegram message."""
    if not token or not chat_id:
        logger.warning("Telegram not configured")
        return
    import requests
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    logger.info(f"Telegram notification sent to {chat_id}")


def _send_email(recipients: str, subject: str, message: str):
    """Send email notification."""
    if not recipients:
        return
    from django.core.mail import send_mail
    email_list = [e.strip() for e in recipients.split(",") if e.strip()]
    send_mail(
        subject=f"[FakeGuard] {subject}",
        message=message,
        from_email="noreply@fakeguard.app",
        recipient_list=email_list,
        fail_silently=True,
    )
    logger.info(f"Email sent to {email_list}")
