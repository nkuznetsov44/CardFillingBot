from typing import Optional
import re
from datetime import datetime
from telegramapi.types import Message
from message_parsers import IMessageParser, IParsedMessage
from dto import FillDto, UserDto
from services.card_fill_service import CardFillService


number_regexp = re.compile(r'[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?')


class FillMessageParser(IMessageParser[FillDto]):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[IParsedMessage[FillDto]]:
        """Returns FillDto on successful parse or None if no fill was found."""
        message_text = message.text
        cnt = 0
        for number_match in re.finditer(number_regexp, message_text):
            cnt += 1
            amount = number_match.group()
            before_phrase = message_text[:number_match.start()].strip()
            after_phrase = message_text[number_match.end():].strip()
            if len(before_phrase) > 0 and len(after_phrase) > 0:
                description = ' '.join([before_phrase, after_phrase])
            else:
                description = before_phrase + after_phrase
        if cnt == 1:
            scope = self.card_fill_service.get_scope(message.chat.chat_id)
            fill = FillDto(
                id=None,
                user=UserDto.from_telegramapi(message.from_user),
                fill_date=datetime.fromtimestamp(message.date),
                amount=float(amount),
                description=description,
                category=None,
                scope=scope
            )
            return IParsedMessage(original_message=message, data=fill)
        return None
