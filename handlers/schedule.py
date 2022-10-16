import logging
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app import bot, cache_service, card_fill_service
from services.schedule_service import schedule_message
from formatters import month_names
from dto import Month
from callbacks import schedule_day_cb, schedule_month_cb, Callback


logger = logging.getLogger(__name__)


async def handle_schedule_fill(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    text = f"Выберите планируемый месяц для траты {fill.amount} р. ({fill.description}): {fill.category.name}."
    months_to_schedule = 3
    current_month_num = datetime.now().month
    keyboard_buttons = []
    for month_num in range(current_month_num, current_month_num + months_to_schedule):
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text=month_names[Month(month_num % 12)],
                    callback_data=schedule_month_cb.new(month=month_num),
                )
            ]
        )
    keyboard_buttons.append(
        [InlineKeyboardMarkup(text="ОТМЕНА", callback_data=Callback.DELETE_FILL.value)]
    )
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
    )


async def handle_schedule_month(
    callback_query: CallbackQuery, callback_data: dict[str, str]
) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    month_number = int(callback_data["month"])
    month_name = month_names[Month(month_number)]
    text = (
        f"Выберите планируемую дату в {month_name} для "
        f"затраты {fill.amount} р. ({fill.description}): {fill.category.name}."
    )
    if month_number == datetime.now().month:
        start_date = datetime.now().day + 1
    else:
        start_date = 1
    end_date = (
        datetime(year=datetime.now().year, month=month_number + 1, day=1)
        - timedelta(days=1)
    ).day
    days = range(start_date, end_date + 1)
    keyboard_buttons = []
    buttons_per_row = 6
    for i in range(0, len(days), buttons_per_row):
        buttons_group = []
        for day in days[i : i + buttons_per_row]:
            buttons_group.append(
                InlineKeyboardButton(
                    text=f"{day}",
                    callback_data=schedule_day_cb.new(month=month_number, day=day),
                )
            )
        keyboard_buttons.append(buttons_group)
    keyboard_buttons.append(
        [InlineKeyboardMarkup(text="ОТМЕНА", callback_data=Callback.DELETE_FILL.value)]
    )
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
    )


async def handle_schedule_day(
    callback_query: CallbackQuery, callback_data: dict[str, str]
) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    month_number = int(callback_data["month"])
    month_name = month_names[Month(month_number)]
    day = int(callback_data["day"])
    scheduled_fill_date = datetime(
        year=datetime.now().year,
        month=month_number,
        day=day,
        hour=19,
        minute=0,
        second=0,
        tzinfo=fill.fill_date.tzinfo,
    )
    text = None
    try:
        card_fill_service.change_date_for_fill(fill, scheduled_fill_date)
        schedule_message(
            chat_id=int(callback_query.message.chat.id),
            text=f"Оповещение о запланированной трате {fill.amount} р. ({fill.description}). Она состоялась?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Да", callback_data=Callback.SCHEDULE_CONFIRM.value
                        ),
                        InlineKeyboardMarkup(
                            text="Нет", callback_data=Callback.SCHEDULE_DECLINE.value
                        ),
                    ]
                ]
            ),
            dt=scheduled_fill_date,
            context={"fill_id": fill.id},
        )
        text = (
            f"Трата {fill.amount} р. ({fill.description}): {fill.category.name} запланирована на "
            f"{month_name}, {day}. Она будет учитываться в статистике за {month_name}. "
            f"В день траты придет запрос для подтверждения."
        )
    except:
        text = "Ошибка добавления запланированной траты."
    finally:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=None,
        )


async def handle_scheduled_fill_confirm(callback_query: CallbackQuery) -> None:
    context = cache_service.get_context_for_message(callback_query.message)
    fill = card_fill_service.get_fill_by_id(context["fill_id"])
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None,
        text=f"Трата {fill.amount} р. ({fill.description}) зафиксирована в {fill.fill_date}.",
    )


async def handle_scheduled_fill_declined(callback_query: CallbackQuery) -> None:
    context = cache_service.get_context_for_message(callback_query.message)
    fill = card_fill_service.get_fill_by_id(context["fill_id"])
    card_fill_service.delete_fill(fill)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None,
        text=f"Запись {fill.amount} р. ({fill.description}) в {fill.fill_date} удалена.",
    )
