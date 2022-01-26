import json
import logging
from typing import Optional, List, Any, Dict
import redis
from aiogram.types import Message
from settings import redis_host, redis_port, redis_db, redis_password
from dto import FillDto, CategoryDto, Month


class CacheService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
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
        self.rdb.set(f'{message.chat.id}_{message.message_id}_fill', fill_json)
        self.logger.debug(
            f'Save to cache fill {fill_json} for chat {message.chat.id}, message {message.message_id}'
        )

    def get_fill_for_message(self, message: Message) -> Optional[FillDto]:
        fill_json = self.rdb.get(f'{message.chat.id}_{message.message_id}_fill')
        self.logger.debug(
            f'Get from cache fill {fill_json} for chat {message.chat.id}, message {message.message_id}'
        )
        if not fill_json:
            return None
        return FillDto.from_json(fill_json)

    def set_months_for_message(self, message: Message, months: List[Month]) -> None:
        month_numbers = [str(month.value) for month in months]
        self.rdb.set(f'{message.chat.id}_{message.message_id}_months', ','.join(month_numbers))
        self.logger.debug(
            f'Save to cache months {month_numbers} for chat {message.chat.id}, message {message.message_id}'
        )

    def get_months_for_message(self, message: Message) -> Optional[List[Month]]:
        month_numbers = self.rdb.get(f'{message.chat.id}_{message.message_id}_months').split(',')
        if not month_numbers:
            return None
        self.logger.debug(
            f'Get from cache months {month_numbers} for for chat {message.chat.id}, message {message.message_id}'
        )
        return [Month(int(month_number)) for month_number in month_numbers]

    def set_category_for_message(self, message: Message, category: CategoryDto) -> None:
        category_json = category.to_json()
        self.rdb.set(f'{message.chat.id}_{message.message_id}_category', category_json)
        self.logger.debug(
            f'Save to cache category {category} for message for '
            f'chat {message.chat.id}, message {message.message_id}'
        )

    def get_category_for_message(self, message: Message) -> Optional[CategoryDto]:
        category_json = self.rdb.get(f'{message.chat.id}_{message.message_id}_category')
        self.logger.debug(
            f'Get from cache category {category_json} for for chat {message.chat.id}, message {message.message_id}'
        )
        if not category_json:
            return None
        return CategoryDto.from_json(category_json)

    def set_context_for_message(self, message: Message, context: Dict[str, Any]) -> None:
        context_str = json.dumps(context)
        self.rdb.set(f'{message.chat.id}_{message.message_id}_context', context_str)
        self.logger.debug(
            f'Save to cache context {context_str} for message for '
            f'chat {message.chat.id}, message {message.message_id}'
        )

    def get_context_for_message(self, message: Message) -> Optional[Dict[str, Any]]:
        context_str = self.rdb.get(f'{message.chat.id}_{message.message_id}_context')
        self.logger.debug(
            f'Get from cache context {context_str} for for chat {message.chat.id}, message {message.message_id}'
        )
        return json.loads(context_str)
