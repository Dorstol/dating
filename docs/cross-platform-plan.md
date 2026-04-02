# Cross-Platform Dating App — Implementation Plan

## Architecture

```
dating/
├── app_src/          # FastAPI API (existing)
├── bot/              # Telegram bot (aiogram)
├── web/              # Vue 3 frontend (Telegram WebApp + website)
├── docker-compose.yml
└── pyproject.toml
```

- **API** (FastAPI) — единый бэкенд для всех клиентов
- **Vue WebApp** — фронтенд, работает внутри Telegram WebApp и как обычный сайт
- **Telegram бот** — aiogram, запускает WebApp, отправляет уведомления
- Авторизация: JWT (email) + Telegram initData (параллельно)

## Implementation Order

### Step 1: API — Telegram Auth
- Add `telegram_id` (BigInt, nullable, unique) to User model
- Alembic migration
- `POST /api/v1/auth/telegram` — validate Telegram initData, find or create user, return JWT
- Telegram initData validation via bot token HMAC-SHA256

### Step 2: API — WebSocket Chat
- Message model: id, match_id, sender_id, text, created_at, is_read
- Alembic migration
- `WebSocket /ws/chat/{match_id}` — real-time messaging
- Redis Pub/Sub for multi-worker support
- `GET /api/v1/matches/{match_id}/messages` — chat history with pagination
- Unit tests

### Step 3: Telegram Bot (basic)
- aiogram 3.x setup in `bot/`
- `/start` command — sends WebApp button
- Bot token in shared .env
- Dockerfile for bot

### Step 4: Vue Frontend — Skeleton
- Vite + Vue 3 + Vue Router + Pinia
- Telegram WebApp SDK integration (@twa-dev/sdk)
- Auth flow: initData → API → JWT → store
- Fallback: email auth for non-Telegram access
- Base layout, router guards

### Step 5: Vue Frontend — Screens
- Swipe cards (suggestions) with like/pass
- Match list
- Chat (WebSocket)
- Profile view + edit
- Photo upload

### Step 6: Bot — Notifications
- Notify on new mutual match
- Notify on new message (if user not in WebApp)
- Store notification preferences
- Throttling to avoid spam
