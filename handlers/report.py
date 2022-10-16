from datetime import datetime
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ParseMode,
)
from app import bot, cache_service, card_fill_service, graph_service
from formatters import (
    month_names,
    format_user_fills,
    format_monthly_report,
    format_monthly_report_group,
    format_yearly_report,
)
from dto import UserDto, FillScopeDto
from settings import pay_silivri_scope_id
from callbacks import Callback


async def handle_my_fills_current_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    year = datetime.now().year
    from_user = UserDto.from_telegramapi(callback_query.from_user)
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    fills = card_fill_service.get_user_fills_in_months(from_user, months, year, scope)

    message_text = format_user_fills(fills, from_user, months, year, scope)
    previous_year = InlineKeyboardButton(
        text="Предыдущий год",
        callback_data=Callback.MY_FILLS_PREVIOUS_YEAR.value,
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[previous_year]])
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def handle_my_fills_previous_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    previous_year = datetime.now().year - 1
    from_user = UserDto.from_telegramapi(callback_query.from_user)
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    fills = card_fill_service.get_user_fills_in_months(
        from_user, months, previous_year, scope
    )
    message_text = format_user_fills(fills, from_user, months, previous_year, scope)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def handle_per_month_current_year(callback_query: CallbackQuery) -> None:
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    if scope.scope_id == pay_silivri_scope_id:
        return await _per_month_current_year_group(callback_query, scope)
    return await _per_month_current_year_default(callback_query, scope)


async def _per_month_current_year_group(
    callback_query: CallbackQuery, scope: FillScopeDto
) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    year = datetime.now().year
    data = card_fill_service.get_debt_monthly_report_by_user(months, year, scope)

    message_text = format_monthly_report_group(data, year, scope)
    if len(months) == 1:
        month = months[0]
        diagram = graph_service.create_by_user_diagram(
            data[month], name=f"{month_names[month]} {year}"
        )
        if diagram:
            await bot.send_photo(
                callback_query.message.chat.id,
                photo=diagram,
                caption=message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        else:
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
            )


async def _per_month_current_year_default(
    callback_query: CallbackQuery, scope: FillScopeDto
) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    year = datetime.now().year
    data = card_fill_service.get_monthly_report(months, year, scope)

    message_text = format_monthly_report(data, year, scope)
    previous_year = InlineKeyboardButton(
        text="Предыдущий год", callback_data=Callback.MONTHLY_REPORT_PREVIOUS_YEAR.value
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[previous_year]])

    if len(months) == 1:
        month = months[0]
        diagram = graph_service.create_by_category_diagram(
            data[month].by_category, name=f"{month_names[month]} {year}"
        )
        if diagram:
            sent_message = await bot.send_photo(
                callback_query.message.chat.id,
                photo=diagram,
                caption=message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=keyboard,
            )
            cache_service.set_months_for_message(sent_message, months)
            return

    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboard,
    )
    cache_service.set_months_for_message(sent_message, months)


async def handle_per_month_previous_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    previous_year = datetime.now().year - 1
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    data = card_fill_service.get_monthly_report(months, previous_year, scope)

    message_text = format_monthly_report(data, previous_year, scope)
    if len(months) == 1:
        month = months[0]
        diagram = graph_service.create_by_category_diagram(
            data[month].by_category, name=f"{month_names[month]} {previous_year}"
        )
        if diagram:
            sent_message = await bot.send_photo(
                callback_query.message.chat.id,
                photo=diagram,
                caption=message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            cache_service.set_months_for_message(sent_message, months)
            return

    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    cache_service.set_months_for_message(sent_message, months)


async def handle_per_year(callback_query: CallbackQuery) -> None:
    year = datetime.now().year
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    data = card_fill_service.get_yearly_report(year, scope)
    diagram = graph_service.create_by_category_diagram(data.by_category, name=str(year))
    caption = format_yearly_report(data, year, scope)
    await bot.send_photo(
        callback_query.message.chat.id,
        photo=diagram,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
