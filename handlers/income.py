from typing import Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from handlers.base import BaseMessageHandler, BaseCallbackHandler
from parsers.income import IncomeMessage
from formatters import format_income_confirmed
from callbacks import Callback


class IncomeMessageHandler(BaseMessageHandler[IncomeMessage]):
    async def handle(self, message: IncomeMessage) -> None:
        income = message.data
        income = self.card_fill_service.handle_new_income(income)
        
        reply_text = format_income_confirmed(income)

        delete_income_button = InlineKeyboardButton(
            text="Удалить", callback_data=Callback.DELETE_INCOME.value
        )

        inline_keyboard = [[delete_income_button]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

        sent_message = await self.bot.send_message(
            chat_id=message.original_message.chat.id, 
            text=reply_text, 
            reply_markup=keyboard
        )
        self.cache_service.set_income_for_message(sent_message, income)


class DeleteIncomeCallbackHandler(BaseCallbackHandler, callback=Callback.DELETE_INCOME):
    async def handle(self, callback: CallbackQuery, callback_data: Any | None = None) -> None:
        income = self.cache_service.get_income_for_message(callback.message)
        self.card_fill_service.delete_income(income)
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"Доход {income.amount} ({income.description}) удален.",
            reply_markup=None,
        ) 