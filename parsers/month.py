from typing import Optional, List
import re
from aiogram.types import Message
from dto import Month
from parsers import MessageParser, ParsedMessage


months_regexps = {
    Month.january: r"январ[яеь]",
    Month.february: r"феврал[яеь]",
    Month.march: r"март[ае]?",
    Month.april: r"апрел[яеь]",
    Month.may: r"ма[йяе]",
    Month.june: r"июн[яеь]",
    Month.july: r"июл[яеь]",
    Month.august: r"август[ае]?",
    Month.september: r"сентябр[яеь]",
    Month.october: r"октябр[яеь]",
    Month.november: r"ноябр[яеь]",
    Month.december: r"декабр[яеь]",
}


months_names = {
    Month.january: "Январь",
    Month.february: "Февраль",
    Month.march: "Март",
    Month.april: "Апрель",
    Month.may: "Май",
    Month.june: "Июнь",
    Month.july: "Июль",
    Month.august: "Август",
    Month.september: "Сентябрь",
    Month.october: "Октябрь",
    Month.november: "Ноябрь",
    Month.december: "Декабрь",
}


class MonthMessage(ParsedMessage):
    def __init__(self, original_message: Message, data: list[Month]) -> None:
        super().__init__(original_message, data)


class MonthMessageParser(MessageParser):
    def parse(self, message: Message) -> Optional[MonthMessage]:
        """Returns list of months on successful parse or None if no months were found."""
        message_text = message.text
        results: List[Month] = []
        if message_text:
            for word in message_text.split(" "):
                for month in list(Month):
                    result = re.search(months_regexps[month], word, re.IGNORECASE)
                    if result:
                        results.append(month)
        if results:
            return MonthMessage(original_message=message, data=results)
        return None
