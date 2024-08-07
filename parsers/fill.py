from typing import Optional
import re
from aiogram.types import Message
from parsers import MessageParser, ParsedMessage
from entities import Fill, User, FillScope, Currency
from services.card_fill_service import CardFillService


number_with_currency_regexp = re.compile(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[.]?\d*(?:[eE][-+]?\d+)?([reREреРЕ])?")


class FillMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: Fill) -> None:
        super().__init__(original_message, data)


class FillMessageParser(MessageParser):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[FillMessage]:
        """Returns Fill on successful parse or None if no fill was found."""
        message_text = message.text
        cnt = 0
        for number_match in re.finditer(number_with_currency_regexp, message_text):
            cnt += 1
            amount = number_match.group()
            currency = None
            if amount[-1] in ('r', 'R', 'e', 'E', 'р', 'Р', 'Е', 'е'):
                amount, currency_alias = amount[:-1], amount[-1]
                currency = Currency.get_by_alias(currency_alias.lower())
            before_phrase = message_text[: number_match.start()].strip()
            after_phrase = message_text[number_match.end() :].strip()
            if len(before_phrase) > 0 and len(after_phrase) > 0:
                description = " ".join([before_phrase, after_phrase])
            else:
                description = before_phrase + after_phrase
        if cnt == 1:
            scope = self.card_fill_service.get_scope(message.chat.id)
            fill = Fill(
                id=None,
                user=User.from_telegramapi(message.from_user),
                fill_date=message.date,
                amount=float(amount),
                description=description,
                category=None,
                scope=scope,
                currency=currency,
            )
            print(fill)
            return FillMessage(original_message=message, data=fill)
        return None


class NetBalancesMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: FillScope) -> None:
        super().__init__(original_message, data)


class NetBalancesMessageParser(MessageParser):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[NetBalancesMessage]:
        if message.text.lower().startswith("/net"):
            scope = self.card_fill_service.get_scope(message.chat.id)
            return NetBalancesMessage(message, data=scope)
        else:
            return None
