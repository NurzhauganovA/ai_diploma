#!/bin/sh
set -e

echo "================================================"
echo "  FakeGuard Backend — Startup"
echo "================================================"

# Папка для SQLite базы
mkdir -p /app/data
chmod 777 /app/data

# Ждём Redis
echo "⏳ Ожидание Redis..."
until python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; do
  echo "   Redis не готов, ждём 2 сек..."
  sleep 2
done
echo "✅ Redis готов"

# Создаём миграции (на случай если папки migrations не существуют)
echo ""
echo "📝 Создание миграций..."
python manage.py makemigrations users sources articles alerts analytics --noinput 2>/dev/null || true
python manage.py makemigrations --noinput 2>/dev/null || true
echo "✅ Миграции созданы"

# Применяем миграции
echo ""
echo "🗄️  Применение миграций..."
python manage.py migrate --noinput
echo "✅ Миграции применены"

# Инициализация: admin + алерты + реальные данные
echo ""
echo "🌱 Инициализация системы..."
COMPANY="${MONITORED_COMPANY:-Яндекс}"
python manage.py seed_demo --company "$COMPANY"
echo "✅ Инициализация завершена"

echo ""
echo "🚀 Запуск Django на 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000
