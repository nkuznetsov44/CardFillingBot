from typing import Optional, Any
from abc import ABC, abstractmethod
from aiogram.types import Message


class ParsedMessage:
    def __init__(self, original_message: Message, data: Any) -> None:
        self.original_message = original_message
        self.data = data

    def __str__(self) -> str:
        return f'{type(self)}: "{self.original_message.text}" from {self.original_message.from_user}'


class MessageParser(ABC):
    @abstractmethod
    def parse(self, message: Message) -> Optional[ParsedMessage]:
        """Returnes parsed object or None if parsing failed."""
