from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass
import redis
from telegramapi.types import Message
from settings import redis_host, redis_port, redis_db, redis_password
from dto import FillDto, CategoryDto, Month

if TYPE_CHECKING:
    from logging import Logger


@dataclass(frozen=True)
class CacheServiceSettings:
    logger: 'Logger'


class CacheService:
    def __init__(self, cache_service_settings: CacheServiceSettings):
        self.logger = cache_service_settings.logger
        self.rdb = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
            charset='utf-8'
        )
        self.logger.info('Initialized redis connection for cache service')

    def set_fill_for_message(self, message: Message, fill: FillDto) -> None:
        fill_json = fill.to_json()
        self.rdb.set(f'{message.chat.chat_id}_{message.message_id}_fill', fill_json)
        self.logger.debug(
            f'Save to cache fill {fill_json} for chat {message.chat.chat_id}, message {message.message_id}'
        )

    def get_fill_for_message(self, message: Message) -> Optional[FillDto]:
        fill_json = self.rdb.get(f'{message.chat.chat_id}_{message.message_id}_fill')
        self.logger.info(
            f'Get from cache fill {fill_json} for chat {message.chat.chat_id}, message {message.message_id}'
        )
        if not fill_json:
            return None
        return FillDto.from_json(fill_json)

    def set_months_for_message(self, message: Message, months: List[Month]) -> None:
        month_numbers = [str(month.value) for month in months]
        self.rdb.set(f'{message.chat.chat_id}_{message.message_id}_months', ','.join(month_numbers))
        self.logger.debug(
            f'Save to cache months {month_numbers} for chat {message.chat.chat_id}, message {message.message_id}'
        )

    def get_months_for_message(self, message: Message) -> Optional[List[Month]]:
        month_numbers = self.rdb.get(f'{message.chat.chat_id}_{message.message_id}_months').split(',')
        if not month_numbers:
            return None
        self.logger.debug(
            f'Get from cache months {month_numbers} for for chat {message.chat.chat_id}, message {message.message_id}'
        )
        return [Month(int(month_number)) for month_number in month_numbers]

    def set_category_for_message(self, message: Message, category: CategoryDto) -> None:
        category_json = category.to_json()
        self.rdb.set(f'{message.chat.chat_id}_{message.message_id}_category', category_json)
        self.logger.debug(
            f'Save to cache category {category} for message for '
            f'chat {message.chat.chat_id}, message {message.message_id}'
        )

    def get_category_for_message(self, message: Message) -> Optional[CategoryDto]:
        category_json = self.rdb.get(f'{message.chat.chat_id}_{message.message_id}_category')
        self.logger.debug(
            f'Get from cache category {category_json} for for chat {message.chat.chat_id}, message {message.message_id}'
        )
        if not category_json:
            return None
        return CategoryDto.from_json(category_json)
