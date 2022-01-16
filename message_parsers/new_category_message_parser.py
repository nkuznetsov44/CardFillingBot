import logging
from typing import Optional, Tuple
from dto import CategoryDto, FillDto
from aiogram.types import Message
from message_parsers import IMessageParser, IParsedMessage
from services.cache_service import CacheService


class NewCategoryMessageParser(IMessageParser[Tuple[CategoryDto, FillDto]]):
    def __init__(self, cache_service: CacheService) -> None:
        self.logger = logging.getLogger(__name__)
        self.cache_service = cache_service

    def parse(self, message: Message) -> Optional[IParsedMessage[Tuple[CategoryDto, FillDto]]]:
        if not message.reply_to_message:
            return None
        if not message.reply_to_message.text:
            return None
        if not message.reply_to_message.text.startswith('Создание категории для пополнения: '):
            return None
        try:
            cat_name, cat_code, cat_proportion = message.text.split(',')
            cat_name = cat_name.strip()
            cat_code = cat_code.strip()
            cat_proportion = float(cat_proportion.strip())
            fill = self.cache_service.get_fill_for_message(message.reply_to_message)
            aliases = []
            if fill.description:
                aliases.append(fill.description)
            category = CategoryDto(name=cat_name, code=cat_code, aliases=aliases, proportion=cat_proportion)
            return IParsedMessage(original_message=message, data=(category, fill))
        except Exception:
            self.logger.exception('Ошибка создания категории')
            return None
