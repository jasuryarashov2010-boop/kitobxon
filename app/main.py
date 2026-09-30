from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.config import Settings, get_settings
from app.db.session import Database
from app.handlers import admin, channel, errors, user
from app.middlewares.context import AppContextMiddleware


settings: Settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
redis = Redis.from_url(settings.normalized_redis_url, decode_responses=False)
storage = RedisStorage(redis=redis)
dp = Dispatcher(storage=storage)
db = Database(settings)

dp.update.outer_middleware(AppContextMiddleware(settings, db))

dp.include_router(errors.router)
dp.include_router(channel.router)
dp.include_router(admin.router)
dp.include_router(user.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret,
        allowed_updates=["message", "callback_query", "channel_post", "edited_channel_post"],
        drop_pending_updates=False,
    )
    yield
    await bot.delete_webhook(drop_pending_updates=False)
    await storage.close()
    await redis.aclose()
    await bot.session.close()
    await db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(settings.webhook_path)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    if not x_telegram_bot_api_secret_token or not secrets.compare_digest(
        x_telegram_bot_api_secret_token,
        settings.webhook_secret,
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = await request.json()
    from aiogram.types import Update

    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
