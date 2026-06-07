#!/bin/sh
# Backend entrypoint — запускается при старте контейнера backend
set -e

echo "================================================"
echo "  FakeGuard Backend — Startup"
echo "================================================"

# Ждём Redis
echo "⏳ Ожидание Redis..."
until python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; do
  echo "   Redis не готов, ждём 2 сек..."
  sleep 2
done
echo "✅ Redis готов"

# Миграции
echo ""
echo "🗄️  Применение миграций..."
python manage.py migrate --noinput
echo "✅ Миграции применены"

# Демо-данные (только если БД пустая)
echo ""
echo "🌱 Загрузка демо-данных..."
python manage.py seed_demo
echo "✅ Данные загружены"

echo ""
echo "🚀 Запуск Django сервера..."
exec python manage.py runserver 0.0.0.0:8000
