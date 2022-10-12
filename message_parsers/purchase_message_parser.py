from aiogram.types import Message
from typing import Optional
from message_parsers import IMessageParser, IParsedMessage
from dto import PurchaseListItemDto
from services.card_fill_service import CardFillService


class PurchaseMessageParser(IMessageParser[PurchaseListItemDto]):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[IParsedMessage[PurchaseListItemDto]]:
        scope = self.card_fill_service.get_scope(message.chat.id)

        if message.text.startswith('-'):
            message_text = message.text
            name = message_text.replace('-', '').strip()
        else:
            return None

        item = PurchaseListItemDto(
            id=None,
            scope=scope,
            name=name
        )

        return IParsedMessage(message, item)
