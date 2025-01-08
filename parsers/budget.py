from typing import Optional
from aiogram.types import Message
from parsers import MessageParser, ParsedMessage
from entities import FillScope
from services.card_fill_service import CardFillService


class BudgetMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: FillScope) -> None:
        super().__init__(original_message, data)


class BudgetMessageParser(MessageParser):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[BudgetMessage]:
        if message.text.lower().startswith("/budget"):
            scope = self.card_fill_service.get_scope(message.chat.id)
            return BudgetMessage(message, data=scope)
        else:
            return None
