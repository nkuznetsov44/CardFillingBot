from typing import Optional
from aiogram.types import Message
from message_parsers import IMessageParser, IParsedMessage


class DeletePurchaseMessageParser(IMessageParser[list[int]]):
    def parse(self, message: Message) -> Optional[IParsedMessage[list[int]]]:
        if not message.reply_to_message:
            return None
        if not message.reply_to_message.text:
            return None
        if not ('Список покупок' in message.reply_to_message.text):
            return None

        return IParsedMessage(
            message, data=[int(i.strip()) for i in message.text.split(',')]
        )

