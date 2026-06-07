from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("articles", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AlertRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, verbose_name="Название правила")),
                ("condition_type", models.CharField(
                    choices=[
                        ("fake_score", "Fake Score"), ("sentiment", "Тональность"),
                        ("toxicity", "Токсичность"), ("keyword", "Ключевое слово"),
                        ("urgency", "Уровень угрозы"),
                    ],
                    max_length=30,
                )),
                ("threshold", models.FloatField(blank=True, null=True)),
                ("keyword", models.CharField(blank=True, max_length=200)),
                ("urgency_level", models.CharField(blank=True, max_length=20)),
                ("sentiment_value", models.CharField(blank=True, max_length=20)),
                ("channel", models.CharField(
                    choices=[("email", "Email"), ("telegram", "Telegram"), ("in_app", "В приложении")],
                    default="in_app", max_length=20,
                )),
                ("telegram_chat_id", models.CharField(blank=True, max_length=100)),
                ("email_recipients", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("notifications_count", models.IntegerField(default=0)),
                ("last_triggered_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("recipients", models.ManyToManyField(
                    blank=True, related_name="alert_rules", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "Правило алерта",
                "verbose_name_plural": "Правила алертов",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("status", models.CharField(
                    choices=[("pending", "Ожидает"), ("sent", "Отправлено"), ("failed", "Ошибка")],
                    default="pending", max_length=20,
                )),
                ("channel", models.CharField(blank=True, max_length=20)),
                ("message", models.TextField(blank=True)),
                ("is_read", models.BooleanField(default=False)),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("article", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notifications",
                    to="articles.article",
                )),
                ("rule", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notifications",
                    to="alerts.alertrule",
                )),
            ],
            options={
                "verbose_name": "Уведомление",
                "verbose_name_plural": "Уведомления",
                "ordering": ["-sent_at"],
            },
        ),
    ]
