import logging
from typing import Optional, Tuple
from dto import CategoryDto, FillDto
from aiogram.types import Message
import emoji
from parsers import MessageParser, ParsedMessage
from services.cache_service import CacheService


class NewCategoryMessage(ParsedMessage):
    def __init__(
        self, original_message: Message, data: Tuple[CategoryDto, FillDto]
    ) -> None:
        super().__init__(original_message, data)


class NewCategoryMessageParser(MessageParser):
    def __init__(self, cache_service: CacheService) -> None:
        self.logger = logging.getLogger(__name__)
        self.cache_service = cache_service

    def parse(self, message: Message) -> Optional[NewCategoryMessage]:
        if not message.reply_to_message:
            return None
        if not message.reply_to_message.text:
            return None
        if not message.reply_to_message.text.startswith(
            "Создание категории для записи: "
        ):
            return None
        try:
            cat_name, cat_code, cat_proportion, cat_emoji = message.text.split(",")
            cat_name = cat_name.strip()
            if not cat_name.isupper():
                cat_name = cat_name.lower()
            cat_code = cat_code.strip().upper()
            cat_proportion = float(cat_proportion.strip())
            cat_emoji = emoji.demojize(cat_emoji.strip())
            fill = self.cache_service.get_fill_for_message(message.reply_to_message)
            aliases = []
            if fill.description:
                aliases.append(fill.description)
            category = CategoryDto(
                name=cat_name,
                code=cat_code,
                aliases=aliases,
                proportion=cat_proportion,
                emoji_name=cat_emoji,
            )
            return NewCategoryMessage(original_message=message, data=(category, fill))
        except Exception:
            self.logger.exception("Ошибка создания категории")
            return None
