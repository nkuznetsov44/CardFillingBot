import logging
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.bot import Bot
from aiogram.utils.executor import start_webhook
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from settings import (
    webhook_path, webhook_url, webapp_host, webapp_port,
    telegram_token, database_uri, scheduler_clear_jobs, log_level
)
from services.card_fill_service import CardFillService
from services.cache_service import CacheService
from services.graph_service import GraphService


level = logging.getLevelName(log_level)
logging.basicConfig(level=level)
logger = logging.getLogger(__name__)

bot = Bot(token=telegram_token)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

card_fill_service = CardFillService()
cache_service = CacheService()
graph_service = GraphService()

scheduler = AsyncIOScheduler({
    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': database_uri
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.asyncio:AsyncIOExecutor',
    },
    'apscheduler.timezone': 'Europe/Moscow',
})


async def on_startup(_: Dispatcher) -> None:
    await bot.set_webhook(webhook_url)
    scheduler.start()
    logger.info('Started scheduler')
    if scheduler_clear_jobs:
        scheduler.remove_all_jobs()
        logger.info('Removed old scheduler jobs')


async def on_shutdown(_: Dispatcher) -> None:
    await bot.delete_webhook(webhook_url)


def start_app() -> None:
    start_webhook(
        dispatcher=dp,
        webhook_path=webhook_path,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=webapp_host,
        port=webapp_port,
        skip_updates=True
    )
