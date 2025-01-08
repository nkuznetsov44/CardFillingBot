from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.base import BaseMessageHandler
from parsers.month import MonthMessage
from formatters import month_names
from callbacks import Callback


class MonthsMessageHandler(BaseMessageHandler[MonthMessage]):
    async def handle(self, message: MonthMessage) -> None:
        months = message.data
        my = InlineKeyboardButton(text="Мои затраты", callback_data=Callback.MY_FILLS.value)
        stat = InlineKeyboardButton(
            text="Отчет за месяцы", callback_data=Callback.MONTHLY_REPORT.value
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[my], [stat]])
        sent_message = await self.bot.send_message(
            chat_id=message.original_message.chat.id,
            text=f'Выбраны месяцы: {", ".join(map(month_names.get, months))}. Какая информация интересует?',
            reply_markup=keyboard,
        )
        self.cache_service.set_months_for_message(sent_message, months)
