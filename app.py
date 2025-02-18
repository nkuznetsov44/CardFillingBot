import logging
from aiogram import Bot, Dispatcher
from settings import settings
from services.card_fill_service import CardFillService
from services.cache_service import CacheService
from services.graph_service import GraphService
from services.state_service import StateService
from entities import AppMode


class App:
    def __init__(self) -> None:
        self.logger = self._init_logger()

        self.bot = Bot(settings.telegram_token)
        self.dp = Dispatcher()

        self.card_fill_service = CardFillService()
        self.cache_service = CacheService()
        self.graph_service = GraphService()
        self.state_service = StateService(self.cache_service)

    @classmethod
    def _init_logger(cls) -> logging.Logger:
        level = logging.getLevelName(settings.log_level)
        logging.basicConfig(level=level)
        return logging.getLogger(__name__)

    async def start(self) -> None:
        if settings.app_mode == AppMode.WEBHOOK:
            raise NotImplementedError
        elif settings.app_mode == AppMode.POLLING:
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self.dp.start_polling(self.bot)
