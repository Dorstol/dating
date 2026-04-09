# Dating App

Cross-platform dating application with FastAPI backend, Telegram Bot, and Vue 3 frontend.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0 (async), Pydantic 2 |
| Database | PostgreSQL (asyncpg) |
| Cache / Messaging | Redis (Pub/Sub, caching, rate limiting) |
| Auth | fastapi-users (JWT), Telegram WebApp initData (HMAC-SHA256) |
| Bot | aiogram 3.x |
| Frontend | Vue 3, Vite, Pinia, Vue Router |
| Monitoring | Prometheus metrics |
| CI | GitHub Actions (ruff, mypy, pytest) |

## Quick Start

```bash
# Start all services
docker compose up

# Or run locally
./setup-dev.sh          # install dependencies
uv run alembic upgrade head  # apply migrations
uv run python app_src/main.py  # start API (dev mode)
```

### Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |
| Adminer | http://localhost:8080 |
| Redis Commander | http://localhost:8081 |

### Running the Bot

```bash
BOT_TOKEN=<your_token> uv run python -m bot
```

### Running the Frontend

```bash
cd web
npm install
npm run dev  # http://localhost:5173
```

## API Endpoints

### Auth (`/api/v1/auth`)
- `POST /login` - Email/password login
- `POST /register` - Registration
- `POST /telegram` - Telegram WebApp auth

### Users (`/api/v1/users`)
- `GET /{user_id}` - Get profile
- `PATCH /me` - Update profile
- `POST /me/upload_photo` - Upload photo
- `POST /{user_id}/block` / `DELETE /{user_id}/block` - Block/unblock
- `POST /{user_id}/report` - Report user

### Matches (`/api/v1/matches`)
- `GET /suggestion` - Get match suggestions
- `POST /{matched_user_id}` - Like user
- `GET /` - List matches

### Chat (`/api/v1/chat`)
- `WS /ws/{match_id}?token=<token>` - Real-time WebSocket chat
- `GET /{match_id}/history` - Message history
- `POST /{match_id}/read` - Mark as read

### Interests (`/api/v1/interests`)
- `GET /popular` - Popular interests
- `GET /search?q=...` - Search
- `GET /my` / `PUT /my` - User interests

### Monitoring
- `GET /metrics` - Prometheus metrics

## Project Structure

```
app_src/
  api/api_v1/       # REST & WebSocket endpoints
  core/
    models/          # SQLAlchemy models (User, Match, Message, Block, Report)
    schemas/         # Pydantic schemas
    config.py        # Settings (DB, auth, rate limits, CORS)
  crud/services/     # Business logic
  alembic/           # Database migrations
  tests/             # Backend tests
bot/
  handlers.py        # /start command, WebApp button
  notifications.py   # Redis Pub/Sub → Telegram notifications
  tests/
web/                 # Vue 3 frontend
scripts/
  seed.py            # Generate test data
```

## Key Features

**Matching** - Interest-based algorithm sorted by rating. Suggestions cached in Redis (5 min TTL). Rate-limited.

**Chat** - WebSocket with Redis Pub/Sub for multi-worker support. Message persistence, read status, paginated history.

**Notifications** - API publishes events to Redis, bot consumes and sends Telegram messages. Throttled: max 1 per user/type per 60s. Triggers: mutual match, new message (when recipient offline).

**Auth** - Dual: email/password (JWT) and Telegram WebApp initData validation. Token-based WebSocket auth via query parameter.

**Moderation** - User blocking (bidirectional, excluded from suggestions) and reporting with reason categories.

## Development

```bash
# Tests
uv run pytest                    # all (136 tests)
uv run pytest app_src/tests/     # backend only
uv run pytest bot/tests/         # bot only

# Linting & formatting
uv run ruff check app_src/ bot/
uv run ruff format app_src/ bot/

# Type checking
uv run mypy app_src/ bot/ --ignore-missing-imports

# Migrations
uv run alembic upgrade head      # apply
uv run alembic downgrade -1      # rollback
uv run alembic revision -m "description"  # create

# Seed test data
uv run python scripts/seed.py
```

## Environment Variables

Configuration uses nested prefix `APP_CONFIG__` with `__` delimiter:

```env
# Database
APP_CONFIG__DB__URL=postgresql+asyncpg://user:password@localhost:5432/dating

# Auth
APP_CONFIG__SECRET_KEY=your-secret
APP_CONFIG__ACCESS_TOKEN__LIFETIME_SECONDS=3600

# Redis
APP_CONFIG__REDIS_URL=redis://localhost:6379

# CORS
APP_CONFIG__CORS__ALLOWED_ORIGINS='["https://your-domain.com"]'

# Bot
BOT_TOKEN=your-telegram-bot-token
WEBAPP_URL=https://your-domain.com
REDIS_URL=redis://localhost:6379
```

## CI

GitHub Actions runs on every push to `main` and on PRs:

| Job | Tool | Blocking |
|-----|------|----------|
| Lint | ruff check + format | Yes |
| Type Check | mypy | No (soft-fail) |
| Tests | pytest | Yes |
