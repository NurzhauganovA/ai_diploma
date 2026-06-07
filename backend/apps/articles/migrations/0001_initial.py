from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("sources", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Article",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("url", models.URLField(max_length=1000, unique=True)),
                ("title", models.CharField(max_length=500)),
                ("content", models.TextField(blank=True)),
                ("summary", models.TextField(blank=True, max_length=500)),
                ("author", models.CharField(blank=True, max_length=200)),
                ("image_url", models.URLField(blank=True, max_length=500)),
                ("language", models.CharField(default="ru", max_length=10)),
                ("status", models.CharField(
                    choices=[("pending", "Ожидает обработки"), ("processed", "Обработана"), ("failed", "Ошибка")],
                    default="pending", max_length=20,
                )),
                ("fake_score", models.FloatField(blank=True, null=True)),
                ("sentiment", models.CharField(blank=True, max_length=20)),
                ("sentiment_score", models.FloatField(blank=True, null=True)),
                ("toxicity_score", models.FloatField(blank=True, null=True)),
                ("urgency", models.CharField(
                    choices=[("low", "Низкая"), ("medium", "Средняя"), ("high", "Высокая"), ("critical", "Критическая")],
                    default="low", max_length=20,
                )),
                ("topic", models.CharField(blank=True, max_length=100)),
                ("entities", models.JSONField(blank=True, default=list)),
                ("keywords", models.JSONField(blank=True, default=list)),
                ("shap_data", models.JSONField(blank=True, default=dict)),
                ("is_verified", models.BooleanField(blank=True, null=True)),
                ("is_about_company", models.BooleanField(default=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("collected_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("source", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="articles",
                    to="sources.source",
                )),
            ],
            options={
                "verbose_name": "Статья",
                "verbose_name_plural": "Статьи",
                "ordering": ["-collected_at"],
            },
        ),
    ]
