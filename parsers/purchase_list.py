import logging
from typing import Optional
from aiogram.types import Message
from parsers import MessageParser, ParsedMessage
from entities import PurchaseListItem, FillScope
from services.card_fill_service import CardFillService


logger = logging.getLogger(__name__)


class PurchaseMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: PurchaseListItem) -> None:
        super().__init__(original_message, data)


class PurchaseMessageParser(MessageParser):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[PurchaseMessage]:
        scope = self.card_fill_service.get_scope(message.chat.id)

        if message.text.startswith("-"):
            message_text = message.text
            name = message_text.replace("-", "").strip()
        else:
            return None

        item = PurchaseListItem(id=None, scope=scope, name=name)

        return PurchaseMessage(message, item)


class PurchaseListMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: FillScope) -> None:
        super().__init__(original_message, data)


class PurchaseListParser(MessageParser):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[PurchaseListMessage]:
        if message.text.lower() in ("список", "list"):
            scope = self.card_fill_service.get_scope(message.chat.id)
            return PurchaseListMessage(message, data=scope)
        else:
            return None


class DeletePurchaseMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: list[int]) -> None:
        super().__init__(original_message, data)


class DeletePurchaseMessageParser(MessageParser):
    def parse(self, message: Message) -> Optional[DeletePurchaseMessage]:
        if not message.reply_to_message:
            return None
        if not message.reply_to_message.text:
            return None
        if not ("Список покупок" in message.reply_to_message.text):
            return None

        try:
            return DeletePurchaseMessage(
                message, data=[int(i.strip()) for i in message.text.split(",")]
            )
        except ValueError:
            logger.warning(
                "Failed to convert delete purchase message to list of ints",
                exc_info=True,
            )
            return None
