from typing import Optional
from aiogram.types import Message
from parsers import MessageParser, ParsedMessage
from entities import ServiceCommandType


class ServiceCommandMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: ServiceCommandType) -> None:
        super().__init__(original_message, data)


class ServiceCommandMessageParser(MessageParser):
    def parse(self, message: Message) -> Optional[ServiceCommandMessage]:
        if (txt := message.text.lower()).startswith("/"):
            try:
                command = ServiceCommandType(txt.split()[0][1:])
            except ValueError:
                return None
            return ServiceCommandMessage(message, data=command)
        else:
            return None
