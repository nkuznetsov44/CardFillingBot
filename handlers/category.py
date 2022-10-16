import logging
from emoji import emojize
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app import bot, cache_service, card_fill_service
from parsers.category import NewCategoryMessage
from formatters import format_fill_confirmed
from callbacks import Callback


logger = logging.getLogger(__name__)


async def handle_new_category_message(parsed_message: NewCategoryMessage) -> None:
    category, fill = parsed_message.data
    text = (
        "Создаём новую категорию:\n"
        f"  - название: {category.name}\n  - код: {category.code}\n"
        f"  - иконка: {category.get_emoji()}\n"
        f"  - пропорция: {category.proportion:.2f}.\n\n"
        "Все верно?"
    )
    confirm = InlineKeyboardButton(
        text="Да", callback_data=Callback.CONFIRM_CATEGORY.value
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[confirm]])
    sent_message = await bot.send_message(
        chat_id=parsed_message.original_message.chat.id,
        text=text,
        reply_markup=keyboard,
        reply_to_message_id=parsed_message.original_message.message_id,
    )
    cache_service.set_fill_for_message(sent_message, fill)
    cache_service.set_category_for_message(sent_message, category)


async def handle_create_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=(
            f"Создание категории для записи: {fill.amount} р. ({fill.description}).\n"
            "Ответом на это сообщение пришлите название, код и пропорцию для новой категории через запятую, "
            f'например "Еда, FOOD, 0.8, {emojize(":carrot:")}".'
        ),
        reply_markup=None,
    )


async def handle_confirm_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    category = cache_service.get_category_for_message(callback_query.message)

    card_fill_service.create_new_category(category)
    fill = card_fill_service.change_category_for_fill(
        fill_id=fill.id, target_category_code=category.code
    )
    budget = card_fill_service.get_budget_for_category(fill.category, fill.scope)
    current_category_usage = (
        card_fill_service.get_current_month_budget_usage_for_category(
            fill.category, fill.scope
        )
    )
    text = format_fill_confirmed(fill, budget, current_category_usage)
    text += f"\nСоздана новая категория {category.get_emoji()} {category.name}."

    message = await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=None,
    )
    cache_service.set_fill_for_message(message, fill)  # caching updated fill
