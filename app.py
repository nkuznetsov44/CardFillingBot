import logging
from uuid import uuid4
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.bot import Bot
from aiogram.utils.executor import start_webhook
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from settings import (
    webhook_path, webhook_url, webapp_host, webapp_port,
    telegram_token, database_uri
)
from services.card_fill_service import CardFillService
from services.cache_service import CacheService
from services.graph_service import GraphService


logging.basicConfig(level=logging.DEBUG)
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
    'apscheduler.timezone': 'Europe/Moscow'
})


async def send_scheduled_message(text: str, chat_id: int) -> None:
    logger.info('Enter job')
    await dp.bot.send_message(chat_id=chat_id, text=text)


async def on_startup(_: Dispatcher) -> None:
    await bot.set_webhook(webhook_url)
    scheduler.remove_all_jobs()
    scheduler.add_job(
        func=send_scheduled_message,
        trigger='interval',
        seconds=10,
        # trigger='date',
        # run_date=datetime(2022, 1, 16, 23, 28, 0),
        args=('test111', 86070242),
        kwargs={},
        id=str(uuid4()),
        name='test_job',
        coalesce=False
    )


async def on_shutdown(_: Dispatcher) -> None:
    await bot.delete_webhook(webhook_url)


def start_app() -> None:
    scheduler.start()
    start_webhook(
        dispatcher=dp,
        webhook_path=webhook_path,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=webapp_host,
        port=webapp_port,
    )
