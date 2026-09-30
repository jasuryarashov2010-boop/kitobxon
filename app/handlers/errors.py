from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)
router = Router(name="errors")


@router.error()
async def global_error_handler(event: ErrorEvent) -> bool:
    logger.exception("Unhandled Telegram update error", exc_info=event.exception)
    return True
