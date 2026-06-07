#!/bin/bash
# FakeGuard — Скрипт быстрой установки для разработки
set -e

echo "======================================"
echo "  FakeGuard — Установка и запуск"
echo "======================================"

# Backend setup
echo ""
echo "📦 [1/4] Устанавливаем Python зависимости..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🗄️  [2/4] Настраиваем базу данных..."
python manage.py migrate
python manage.py seed_demo

echo ""
echo "✅ [3/4] Backend готов!"
echo "   Запустите в отдельном терминале:"
echo "   cd backend && source venv/bin/activate && python manage.py runserver"
echo ""
echo "   (опционально) Celery worker:"
echo "   cd backend && source venv/bin/activate && celery -A config worker -l info"

# Frontend setup
echo ""
echo "📦 [4/4] Устанавливаем Node зависимости..."
cd ../frontend
npm install

echo ""
echo "======================================"
echo "✅ Установка завершена!"
echo "======================================"
echo ""
echo "Запуск Backend:   cd backend && source venv/bin/activate && python manage.py runserver"
echo "Запуск Frontend:  cd frontend && npm run dev"
echo ""
echo "Адреса:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/api/docs/"
echo "  Admin:     http://localhost:8000/admin/"
echo ""
echo "Логин: admin / admin123"
