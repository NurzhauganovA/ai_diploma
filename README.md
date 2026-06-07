# FakeGuard — AI Мониторинг фейков и негативного контента

> Дипломный проект: «Внедрение системы AI-мониторинга фейковых и негативных данных для компании с использованием машинного обучения и анализа текстовых данных»

---

## Запуск одной командой (Docker)

```bash
# Клонировать и запустить
git clone <repo>
cd ai_diploma

docker compose up --build
```

Подождать 1–2 минуты пока соберётся. Затем открыть:

| Сервис | URL |
|--------|-----|
| **Приложение** | http://localhost |
| API Документация | http://localhost/api/docs/ |
| Django Admin | http://localhost/admin/ |

**Логин:** `admin` / **Пароль:** `admin123`

---

## Архитектура Docker

```
http://localhost  (порт 80)
       │
    [Nginx]
    /        → React (статика, production build)
    /api/    → Django Backend :8000
    /admin/  → Django Admin :8000

[Django]     — migrate + seed_demo при старте
[Celery]     — фоновый анализ статей (ML pipeline)
[Celery-Beat]— периодический обход источников
[Redis]      — брокер очередей + кэш
```

---

## Стек технологий

| Слой | Технологии |
|------|-----------|
| Backend | Django 5 · DRF · JWT · Celery · Redis |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · Recharts |
| ML | Fake detection · Sentiment · Toxicity · NER · SHAP |
| Инфраструктура | Docker Compose · Nginx · SQLite |

---

## Запуск без Docker (для разработки)

```bash
# Установить зависимости
sudo apt install python3-pip python3-venv nodejs npm

# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver      # → http://localhost:8000

# Frontend (новый терминал)
cd frontend
npm install
npm run dev                     # → http://localhost:3000

# Celery (опционально, новый терминал)
cd backend && source venv/bin/activate
celery -A config worker -l info
```

---

## Структура проекта

```
ai_diploma/
├── docker/
│   ├── Dockerfile.backend    — образ Django
│   ├── Dockerfile.frontend   — multi-stage: Vite build → Nginx
│   ├── nginx.conf            — проксирование /api/ + статика
│   └── entrypoint.sh         — migrate + seed + runserver
├── backend/
│   ├── apps/
│   │   ├── users/            — JWT auth, роли
│   │   ├── sources/          — источники, RSS краулер
│   │   ├── articles/         — статьи + ML результаты
│   │   ├── alerts/           — правила + уведомления
│   │   └── analytics/        — дашборд API
│   ├── ml/
│   │   ├── analyzer.py       — fake/sentiment/toxicity/NER/SHAP
│   │   └── crawler.py        — RSS + веб краулер
│   └── config/               — settings, urls, celery
└── frontend/
    └── src/
        ├── pages/            — Dashboard, Articles, Sources, Alerts...
        ├── api/              — axios клиент
        ├── store/            — Zustand auth
        └── utils/            — форматирование, цвета
```

---

## Функционал системы

- **Дашборд** — репутационный индекс, тренды угроз, диаграммы тональности
- **Лента угроз** — статьи с Fake Score, тональностью, уровнем угрозы
- **Добавление URL** — вставить ссылку → ML-анализ за секунды
- **Источники** — RSS/сайты, настройка интервала, ручной обход
- **Алерты** — правила (fake_score ≥ N, ключевое слово, etc.)
- **Уведомления** — in-app + Telegram + Email
- **ML объяснения** — SHAP-style: какие слова подняли Fake Score
