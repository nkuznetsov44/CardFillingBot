from typing import Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from handlers.base import BaseMessageHandler, BaseCallbackHandler
from parsers.fill import FillMessage, NetBalancesMessage
from formatters import format_fill_confirmed
from callbacks import ChangeCategoryCallback, Callback


class FillMessageHandler(BaseMessageHandler[FillMessage]):
    async def handle(self, message: FillMessage) -> None:
        fill = message.data
        fill = self.card_fill_service.handle_new_fill(fill)
        budget = self.card_fill_service.get_budget_for_category(fill.category, fill.scope)
        current_category_usage = (
            self.card_fill_service.get_current_month_budget_usage_for_category(
                fill.category, fill.scope
            )
        )
        reply_text = format_fill_confirmed(fill, budget, current_category_usage)

        change_category_button = InlineKeyboardButton(
            text="Сменить категорию", callback_data=Callback.SHOW_CATEGORY.value
        )
        delete_fill_button = InlineKeyboardButton(
            text="Удалить", callback_data=Callback.DELETE_FILL.value
        )

        inline_keyboard = [[change_category_button], [delete_fill_button]]

        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

        sent_message = await self.bot.send_message(
            chat_id=message.original_message.chat.id, text=reply_text, reply_markup=keyboard
        )
        self.cache_service.set_fill_for_message(sent_message, fill)


class NetBalancesMessageHandler(BaseMessageHandler[NetBalancesMessage]):
    async def handle(self, message: NetBalancesMessage) -> None:
        self.card_fill_service.net_balances(message.data)
        await self.bot.send_message(
            chat_id=message.original_message.chat.id,
            text="Текущие траты исключены из расчета баланса",
        )


class ShowCategoryCallbackHandler(BaseCallbackHandler, callback=Callback.SHOW_CATEGORY):
    async def handle(self, callback: CallbackQuery, callback_data: Optional[Any] = None) -> None:
        fill = self.cache_service.get_fill_for_message(callback.message)
        categories = self.card_fill_service.list_categories()

        keyboard_buttons = []
        buttons_per_row = 2
        for i in range(0, len(categories), buttons_per_row):
            buttons_group = []
            for cat in categories[i : i + buttons_per_row]:
                buttons_group.append(
                    InlineKeyboardButton(
                        text=f"{cat.get_emoji()} {cat.name}",
                        callback_data=ChangeCategoryCallback(category_code=cat.code).pack()
                    )
                )
            keyboard_buttons.append(buttons_group)
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="СОЗДАТЬ НОВУЮ КАТЕГОРИЮ",
                    callback_data=Callback.NEW_CATEGORY.value,
                )
            ]
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        reply_text = (
            f"Принято {fill.amount}р. от @{fill.user.username}.\nВыберите категорию"
        )
        if fill.description:
            reply_text += f" для <{fill.description}>"
        reply_text += ":"

        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=reply_text,
            reply_markup=keyboard,
        )


# class ChangeCategoryCallbackHandler(BaseCallbackHandler, callback=Callback.CHANGE_CATEGORY):
#     async def handle(self, callback: CallbackQuery, callback_data: Any | None = None) -> None:
#         pass

async def handle_change_category(
    self, callback_query: CallbackQuery, callback_data: dict[str, str]
) -> None:
    category_code = callback_data["category_code"]
    fill = cache_service.get_fill_for_message(callback_query.message)
    fill = card_fill_service.change_category_for_fill(fill.id, category_code)

    budget = card_fill_service.get_budget_for_category(fill.category, fill.scope)
    current_category_usage = (
        card_fill_service.get_current_month_budget_usage_for_category(
            fill.category, fill.scope
        )
    )

    reply_text = format_fill_confirmed(fill, budget, current_category_usage)

    change_category_button = InlineKeyboardButton(
        text="Сменить категорию", callback_data=Callback.SHOW_CATEGORY.value
    )
    delete_fill_button = InlineKeyboardButton(
        text="Удалить", callback_data=Callback.DELETE_FILL.value
    )
    inline_keyboard = [[change_category_button], [delete_fill_button]]

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    message = await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=reply_text,
        reply_markup=keyboard,
    )
    cache_service.set_fill_for_message(message, fill)  # caching updated fill


async def handle_delete_fill(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    card_fill_service.delete_fill(fill)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Запись {fill.amount} р. ({fill.description}) удалена.",
        reply_markup=None,
    )
