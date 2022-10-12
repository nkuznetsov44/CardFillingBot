from aiogram.types import Message
from typing import Optional
from message_parsers import IMessageParser, IParsedMessage
from dto import FillScopeDto
from services.card_fill_service import CardFillService


class PurchaseListParser(IMessageParser[FillScopeDto]):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[IParsedMessage[FillScopeDto]]:
        scope = self.card_fill_service.get_scope(message.chat.id)

        if message.text.lower() == 'список':
            return IParsedMessage(message, data=scope)
        else:
            return None
