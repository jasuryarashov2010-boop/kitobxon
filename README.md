# 📚 Kitobxon Tavsiya Bot

Telegram bot for a book/literature channel.

## Core flow

1. User opens `/start`.
2. User must join the required channel.
3. User presses `📖 Kitob tavsiya qilish`.
4. Bot collects: book title, author, recommendation text, optional cover image.
5. Recommendation goes to admin(s) for moderation.
6. Admin chooses `✅ Kanalga joylash` or `❌ Rad etish`.
7. Approved recommendation is published to the channel.
8. Bot automatically puts `🔥` reaction on channel posts.

## Stack

- Python 3.13
- aiogram 3.31
- FastAPI webhook for Render
- PostgreSQL + SQLAlchemy async/asyncpg
- Redis/Render Key Value for FSM state

## Required Telegram setup

The bot must be an administrator in the required channel. This is needed for reliable membership checks and for publishing posts. Channel reactions must allow `🔥` and the bot needs permission to react/post as applicable.

## Local run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python -m app
```

For local webhook testing, expose the app through an HTTPS tunnel and put its public URL into `WEBHOOK_BASE_URL`.

## Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Recommended environment variables are listed in `.env.example`.

Render's Free Postgres and Free Key Value instances have important durability limitations; Free Key Value is in-memory and loses state on restart, while Free Postgres has no backups. Use paid datastores if you need durable production data.
