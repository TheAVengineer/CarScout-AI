"""
CarScout AI - Telegram Bot
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from apps.bot.handlers import start, watch, plan
from configs.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main bot entry point"""
    logger.info("Starting CarScout AI Telegram Bot...")
    
    # Initialize bot and dispatcher inside async context
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register handlers
    dp.include_router(start.router)
    dp.include_router(watch.router)
    dp.include_router(plan.router)
    
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
