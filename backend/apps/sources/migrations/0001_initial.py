from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Source",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, verbose_name="Название")),
                ("url", models.URLField(max_length=500, verbose_name="URL")),
                ("source_type", models.CharField(
                    choices=[("rss", "RSS лента"), ("web", "Веб-сайт"), ("telegram", "Telegram"), ("manual", "Ручной ввод")],
                    default="rss", max_length=20,
                )),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("crawl_interval", models.IntegerField(default=1800)),
                ("credibility_score", models.FloatField(default=0.7)),
                ("articles_count", models.IntegerField(default=0)),
                ("last_crawled_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Источник",
                "verbose_name_plural": "Источники",
                "ordering": ["-created_at"],
            },
        ),
    ]
