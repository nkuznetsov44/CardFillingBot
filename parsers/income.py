from typing import Optional
import re
from datetime import datetime
from aiogram.types import Message
from parsers import MessageParser, ParsedMessage
from entities import Income, User, FillScope, Currency
from services.card_fill_service import CardFillService


# Updated regex to match /income amount[currency] [optional date in YYYY-MM-DD] [optional description]
# Group 1: amount (required)
# Group 2: currency (optional)
# Group 3: date in YYYY-MM-DD format (optional)
# Group 4: description (optional)
income_command_regexp = re.compile(r"^/income\s+([-+]?[.]?[\d]+(?:,\d\d\d)*[.]?\d*(?:[eE][-+]?\d+)?)([reREреРЕ]?)(?:\s+(\d{4}-\d{2}-\d{2}))?(?:\s+(.*))?$")


class IncomeMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: Income) -> None:
        super().__init__(original_message, data)


class IncomeMessageParser(MessageParser):
    def __init__(self, card_fill_service: CardFillService) -> None:
        self.card_fill_service = card_fill_service

    def parse(self, message: Message) -> Optional[IncomeMessage]:
        """Returns Income on successful parse or None if no income command was found."""
        if not message.text:
            return None
            
        message_text = message.text.strip()
        
        # Check if message starts with /income
        if not message_text.lower().startswith("/income"):
            return None
            
        match = income_command_regexp.match(message_text)
        if not match:
            return None
            
        amount_str, currency_alias, date_str, description = match.groups()
        
        # Parse currency
        currency = None
        if currency_alias:
            currency = Currency.get_by_alias(currency_alias.lower())
            
        # Parse date (optional, defaults to message date)
        income_date = message.date
        if date_str:
            try:
                # Parse YYYY-MM-DD format and convert to datetime
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                # Keep the time from message.date but use the specified date
                income_date = parsed_date.replace(
                    hour=message.date.hour,
                    minute=message.date.minute,
                    second=message.date.second,
                    microsecond=message.date.microsecond,
                    tzinfo=message.date.tzinfo
                )
            except ValueError:
                # If date parsing fails, use message date and treat date_str as part of description
                if description:
                    description = f"{date_str} {description}"
                else:
                    description = date_str
            
        # Parse description (optional)
        description = description.strip() if description else None
        
        scope = self.card_fill_service.get_scope(message.chat.id)
        income = Income(
            id=None,
            user=User.from_telegramapi(message.from_user),
            income_date=income_date,
            amount=float(amount_str),
            description=description,
            scope=scope,
            currency=currency,
        )
        
        print(f"Parsed income: {income}")
        return IncomeMessage(original_message=message, data=income) 