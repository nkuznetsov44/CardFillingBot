from typing import TypeVar, Generic, ClassVar, Any, Optional
from aiogram.types import CallbackQuery
from app import App
from abc import ABC, abstractmethod

from parsers import ParsedMessage
from callbacks import Callback


class _BHandler:
    def __init__(self, app: App) -> None:
        self.app = app

    @property
    def cache_service(self):
        return self.app.cache_service

    @property
    def card_fill_service(self):
        return self.app.card_fill_service

    @property
    def bot(self):
        return self.app.bot


TParsedMessage = TypeVar('TParsedMessage', bound=ParsedMessage)


class BaseMessageHandler(_BHandler, Generic[TParsedMessage], ABC):
    @abstractmethod
    async def handle(self, message: TParsedMessage) -> None:
        raise NotImplementedError


class BaseCallbackHandler(_BHandler, ABC):
    callback_filter: ClassVar[Any]

    def __init_subclass__(cls, *, callback: Callback) -> None:
        cls.callback_filter = callback.filter()
        return super().__init_subclass__()

    @abstractmethod
    async def handle(self, callback: CallbackQuery, callback_data: Optional[Any] = None) -> None:
        raise NotImplementedError
