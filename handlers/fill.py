import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app import bot, card_fill_service, cache_service
from settings import schedule_enabled
from parsers.fill import FillMessage
from formatters import format_fill_confirmed
from callbacks import change_category_cb, Callback


logger = logging.getLogger(__name__)


async def handle_fill_message(message: FillMessage) -> None:
    fill = message.data
    fill = card_fill_service.handle_new_fill(fill)
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

    if schedule_enabled:
        schedule_fill_button = InlineKeyboardButton(
            text="Запланировать", callback_data=Callback.SCHEDULE_FILL.value
        )
        inline_keyboard.append([schedule_fill_button])

    keyboard = InlineKeyboardMarkup(inline_keyboard)

    sent_message = await bot.send_message(
        chat_id=message.original_message.chat.id, text=reply_text, reply_markup=keyboard
    )
    cache_service.set_fill_for_message(sent_message, fill)


async def handle_show_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    categories = card_fill_service.list_categories()

    keyboard_buttons = []
    buttons_per_row = 2
    for i in range(0, len(categories), buttons_per_row):
        buttons_group = []
        for cat in categories[i : i + buttons_per_row]:
            buttons_group.append(
                InlineKeyboardButton(
                    text=f"{cat.get_emoji()} {cat.name}",
                    callback_data=change_category_cb.new(category_code=cat.code),
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

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=reply_text,
        reply_markup=keyboard,
    )


async def handle_change_category(
    callback_query: CallbackQuery, callback_data: dict[str, str]
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

    if schedule_enabled:
        schedule_fill_button = InlineKeyboardButton(
            text="Запланировать", callback_data=Callback.SCHEDULE_FILL.value
        )
        inline_keyboard.append([schedule_fill_button])

    keyboard = InlineKeyboardMarkup(inline_keyboard)

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
