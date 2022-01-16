from typing import Optional, TypeVar, Generic
from abc import ABC, abstractmethod
from telegramapi.types import Message


T = TypeVar('T')


class IParsedMessage(Generic[T]):
    def __init__(self, original_message: Message, data: T) -> None:
        self.original_message = original_message
        self.data = data


class IMessageParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, message: Message) -> Optional[IParsedMessage[T]]:
        """Returnes parsed object or None if parsing failed."""
