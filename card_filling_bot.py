import logging
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
from emoji import emojize
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from aiogram.utils.callback_data import CallbackData
from dto import Month, FillDto, CategoryDto, UserDto
from message_parsers import IParsedMessage
from message_parsers.month_message_parser import MonthMessageParser
from message_parsers.fill_message_parser import FillMessageParser
from message_parsers.new_category_message_parser import NewCategoryMessageParser
from message_formatters import (
    month_names, format_user_fills, format_monthly_report, format_yearly_report,
    format_fill_confirmed
)
from app import (
    dp, bot, card_fill_service, cache_service, graph_service, start_app
)
from services.schedule_service import schedule_message


logger = logging.getLogger(__name__)


change_category_cb = CallbackData('change_category', 'category_code')
schedule_month_cb = CallbackData('schedule_month', 'month')
schedule_day_cb = CallbackData('schedule_day', 'month', 'day')


@dp.message_handler()
async def basic_message_handler(message: Message) -> None:
    if message.text:
        logger.info(f'Received message {message.text}')

        new_category_message = NewCategoryMessageParser(cache_service).parse(message)
        if new_category_message:
            logger.info(f'Found new category {new_category_message.data}')
            await handle_new_category_parsed_message(new_category_message)
            return

        fill_message = FillMessageParser(card_fill_service).parse(message)
        if fill_message:
            logger.info(f'Found fill {fill_message.data}')
            await handle_fill_parsed_message(fill_message)
            return

        months_message = MonthMessageParser().parse(message)
        if months_message:
            logger.info(f'Found months {months_message.data}')
            await handle_months_parsed_message(months_message)
            return
    await handle_message_fallback(message)


async def handle_new_category_parsed_message(parsed_message: IParsedMessage[Tuple[CategoryDto, FillDto]]) -> None:
    category, fill = parsed_message.data
    text = (
        'Создаём новую категорию:\n'
        f'  - название: {category.name}\n  - код: {category.code}\n'
        f'  - иконка: {category.get_emoji()}\n'
        f'  - пропорция: {category.proportion:.2f}.\n\n'
        'Все верно?'
    )
    confirm = InlineKeyboardButton(text='Да', callback_data='confirm_new_category')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[confirm]])
    sent_message = await bot.send_message(
        chat_id=parsed_message.original_message.chat.id,
        text=text,
        reply_markup=keyboard,
        reply_to_message_id=parsed_message.original_message.message_id
    )
    cache_service.set_fill_for_message(sent_message, fill)
    cache_service.set_category_for_message(sent_message, category)


async def handle_fill_parsed_message(parsed_message: IParsedMessage[FillDto]) -> None:
    fill = parsed_message.data
    try:
        fill = card_fill_service.handle_new_fill(fill)
        budget = card_fill_service.get_budget_for_category(fill.category, fill.scope)
        current_category_usage = card_fill_service.get_current_month_budget_usage_for_category(
            fill.category, fill.scope
        )
        reply_text = format_fill_confirmed(fill, budget, current_category_usage)

        change_category_button = InlineKeyboardButton(text='Сменить категорию', callback_data='show_category')
        delete_fill_button = InlineKeyboardButton(text='Удалить', callback_data='delete_fill')
        schedule_fill_button = InlineKeyboardButton(text='Запланировать', callback_data='schedule_fill')
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[change_category_button], [delete_fill_button], [schedule_fill_button]]
        )
        sent_message = await bot.send_message(
            chat_id=parsed_message.original_message.chat.id,
            text=reply_text,
            reply_markup=keyboard
        )
        cache_service.set_fill_for_message(sent_message, fill)
    except:
        await bot.send_message(
            chat_id=parsed_message.original_message.chat.id,
            text='Ошибка добавления записи.'
        )
        logger.exception('Ошибка добавления записи.')


async def handle_months_parsed_message(parsed_message: IParsedMessage[List[Month]]) -> None:
    months = parsed_message.data
    my = InlineKeyboardButton(text='Мои затраты', callback_data='my')
    stat = InlineKeyboardButton(text='Отчет за месяцы', callback_data='stat')
    yearly_stat = InlineKeyboardButton(text='С начала года', callback_data='yearly_stat')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[my], [stat], [yearly_stat]])
    sent_message = await bot.send_message(
        chat_id=parsed_message.original_message.chat.id,
        text=f'Выбраны месяцы: {", ".join(map(month_names.get, months))}. Какая информация интересует?',
        reply_markup=keyboard
    )
    cache_service.set_months_for_message(sent_message, months)


async def handle_message_fallback(message: Message) -> None:
    await bot.send_message(
        chat_id=message.chat.id,
        text=(
            'Укажите сумму и комментарий в сообщении, например: "150 макдак", для добавления новой записи, '
            'или один или несколько месяцев, например, "январь февраль", для просмотра статистики.'
        )
    )


@dp.callback_query_handler(lambda cq: cq.data == 'show_category')
async def show_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    categories = card_fill_service.list_categories()

    keyboard_buttons = []
    buttons_per_row = 2
    for i in range(0, len(categories), buttons_per_row):
        buttons_group = []
        for cat in categories[i:i + buttons_per_row]:
            buttons_group.append(
                InlineKeyboardButton(
                    text=f'{cat.get_emoji()} {cat.name}',
                    callback_data=change_category_cb.new(category_code=cat.code)
                )
            )
        keyboard_buttons.append(buttons_group)
    keyboard_buttons.append([InlineKeyboardButton(
        text='СОЗДАТЬ НОВУЮ КАТЕГОРИЮ', callback_data='new_category')
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    reply_text = f'Принято {fill.amount}р. от @{fill.user.username}.\nВыберите категорию'
    if fill.description:
        reply_text += f' для <{fill.description}>'
    reply_text += ':'
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=reply_text,
        reply_markup=keyboard
    )


@dp.callback_query_handler(change_category_cb.filter())
async def change_category(callback_query: CallbackQuery, callback_data: Dict[str, str]) -> None:
    category_code = callback_data['category_code']
    fill = cache_service.get_fill_for_message(callback_query.message)
    fill = card_fill_service.change_category_for_fill(fill.id, category_code)

    budget = card_fill_service.get_budget_for_category(fill.category, fill.scope)
    current_category_usage = card_fill_service.get_current_month_budget_usage_for_category(
        fill.category, fill.scope
    )
    reply_text = format_fill_confirmed(fill, budget, current_category_usage)

    change_category_button = InlineKeyboardButton(text='Сменить категорию', callback_data='show_category')
    delete_fill_button = InlineKeyboardButton(text='Удалить', callback_data='delete_fill')
    schedule_fill_button = InlineKeyboardButton(text='Запланировать', callback_data='schedule_fill')
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[change_category_button], [delete_fill_button], [schedule_fill_button]]
    )
    message = await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=reply_text,
        reply_markup=keyboard
    )
    cache_service.set_fill_for_message(message, fill)  # caching updated fill


@dp.callback_query_handler(lambda cq: cq.data == 'delete_fill')
async def delete_fill(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    card_fill_service.delete_fill(fill)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f'Запись {fill.amount} р. ({fill.description}) удалена.',
        reply_markup=None
    )


@dp.callback_query_handler(lambda cq: cq.data == 'new_category')
async def create_new_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=(
            f'Создание категории для записи: {fill.amount} р. ({fill.description}).\n'
            'Ответом на это сообщение пришлите название, код и пропорцию для новой категории через запятую, '
            f'например "Еда, FOOD, 0.8, {emojize(":carrot:")}".'
        ),
        reply_markup=None
    )


@dp.callback_query_handler(lambda cq: cq.data == 'confirm_new_category')
async def confirm_new_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    category = cache_service.get_category_for_message(callback_query.message)
    try:
        card_fill_service.create_new_category(category)
        fill = card_fill_service.change_category_for_fill(fill_id=fill.id, target_category_code=category.code)
        budget = card_fill_service.get_budget_for_category(fill.category, fill.scope)
        current_category_usage = card_fill_service.get_current_month_budget_usage_for_category(
            fill.category, fill.scope
        )
        text = format_fill_confirmed(fill, budget, current_category_usage)
        text += f'\nСоздана новая категория {category.get_emoji()} {category.name}.'
    except:
        text = 'Ошибка создания категории.'
        logger.exception('Ошибка создания категории')
    message = await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=None
    )
    cache_service.set_fill_for_message(message, fill)  # caching updated fill


@dp.callback_query_handler(lambda cq: cq.data == 'my')
async def my_fills_current_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    year = datetime.now().year
    from_user = UserDto.from_telegramapi(callback_query.from_user)
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    fills = card_fill_service.get_user_fills_in_months(from_user, months, year, scope)

    message_text = format_user_fills(fills, from_user, months, year, scope)
    previous_year = InlineKeyboardButton(
        text='Предыдущий год', callback_data='fills_previous_year'
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[previous_year]])
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2
    )


@dp.callback_query_handler(lambda cq: cq.data == 'fills_previous_year')
async def my_fills_previous_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    previous_year = datetime.now().year - 1
    from_user = UserDto.from_telegramapi(callback_query.from_user)
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    fills = card_fill_service.get_user_fills_in_months(from_user, months, previous_year, scope)
    message_text = format_user_fills(fills, from_user, months, previous_year, scope)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )


@dp.callback_query_handler(lambda cq: cq.data == 'stat')
async def per_month_current_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    year = datetime.now().year
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    data = card_fill_service.get_monthly_report(months, year, scope)

    message_text = format_monthly_report(data, year, scope)
    previous_year = InlineKeyboardButton(text='Предыдущий год', callback_data='previous_year')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[previous_year]])

    if len(months) == 1:
        month = months[0]
        diagram = graph_service.create_by_category_diagram(
            data[month].by_category, name=f'{month_names[month]} {year}'
        )
        if diagram:
            sent_message = await bot.send_photo(
                callback_query.message.chat.id,
                photo=diagram,
                caption=message_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=keyboard
            )
            cache_service.set_months_for_message(sent_message, months)
            return
    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboard
    )
    cache_service.set_months_for_message(sent_message, months)


@dp.callback_query_handler(lambda cq: cq.data == 'previous_year')
async def per_month_previous_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    previous_year = datetime.now().year - 1
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    data = card_fill_service.get_monthly_report(months, previous_year, scope)

    message_text = format_monthly_report(data, previous_year, scope)
    if len(months) == 1:
        month = months[0]
        diagram = graph_service.create_by_category_diagram(
            data[month].by_category, name=f'{month_names[month]} {previous_year}'
        )
        if diagram:
            sent_message = await bot.send_photo(
                callback_query.message.chat.id,
                photo=diagram,
                caption=message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            cache_service.set_months_for_message(sent_message, months)
            return
    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    cache_service.set_months_for_message(sent_message, months)


@dp.callback_query_handler(lambda cq: cq.data == 'yearly_stat')
async def per_year(callback_query: CallbackQuery) -> None:
    year = datetime.now().year
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    data = card_fill_service.get_yearly_report(year, scope)
    diagram = graph_service.create_by_category_diagram(data.by_category, name=str(year))
    caption = format_yearly_report(data, year, scope)
    await bot.send_photo(
        callback_query.message.chat.id, photo=diagram, caption=caption, parse_mode=ParseMode.MARKDOWN_V2
    )


@dp.callback_query_handler(lambda cq: cq.data == 'schedule_fill')
async def schedule_fill(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    text = f'Выберите планируемый месяц для траты {fill.amount} р. ({fill.description}): {fill.category.name}.'
    months_to_schedule = 3
    current_month_num = datetime.now().month
    keyboard_buttons = []
    for month_num in range(current_month_num, current_month_num + months_to_schedule):
        keyboard_buttons.append([InlineKeyboardButton(
            text=month_names[Month(month_num % 12)], callback_data=schedule_month_cb.new(month=month_num)
        )])
    keyboard_buttons.append([InlineKeyboardMarkup(text='ОТМЕНА', callback_data='delete_fill')])
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )


@dp.callback_query_handler(schedule_month_cb.filter())
async def schedule_month(callback_query: CallbackQuery, callback_data: Dict[str, str]) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    month_number = int(callback_data['month'])
    month_name = month_names[Month(month_number)]
    text = (
        f'Выберите планируемую дату в {month_name} для '
        f'затраты {fill.amount} р. ({fill.description}): {fill.category.name}.'
    )
    if month_number == datetime.now().month:
        start_date = datetime.now().day + 1
    else:
        start_date = 1
    end_date = (datetime(year=datetime.now().year, month=month_number + 1, day=1) - timedelta(days=1)).day
    days = range(start_date, end_date + 1)
    keyboard_buttons = []
    buttons_per_row = 6
    for i in range(0, len(days), buttons_per_row):
        buttons_group = []
        for day in days[i:i + buttons_per_row]:
            buttons_group.append(
                InlineKeyboardButton(
                    text=f'{day}',
                    callback_data=schedule_day_cb.new(month=month_number, day=day)
                )
            )
        keyboard_buttons.append(buttons_group)
    keyboard_buttons.append([InlineKeyboardMarkup(text='ОТМЕНА', callback_data='delete_fill')])
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )


@dp.callback_query_handler(schedule_day_cb.filter())
async def schedule_day(callback_query: CallbackQuery, callback_data: Dict[str, str]) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    month_number = int(callback_data['month'])
    month_name = month_names[Month(month_number)]
    day = int(callback_data['day'])
    scheduled_fill_date = datetime(
        year=datetime.now().year, month=month_number, day=day,
        hour=19, minute=0, second=0
    )
    card_fill_service.change_date_for_fill(fill, scheduled_fill_date)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=(
            f'Трата {fill.amount} р. ({fill.description}): {fill.category.name} запланирована на '
            f'{month_name}, {day}. Она будет учитываться в статистике за {month_name}. '
            f'В день траты придет запрос для подтверждения.'
        ),
        reply_markup=None
    )
    schedule_message(
        chat_id=int(callback_query.message.chat.id),
        text=f'Оповещение о запланированной трате {fill.amount} р. ({fill.description}). Она состоялась?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text='Да', callback_data='scheduled_fill_callback_yes'),
                InlineKeyboardMarkup(text='Нет', callback_data='scheduled_fill_callback_no')
            ]]
        ),
        dt=scheduled_fill_date,
        context={
            'fill_id': fill.id
        }
    )


@dp.callback_query_handler(lambda cq: cq.data == 'scheduled_fill_callback_yes')
async def scheduled_fill_callback_yes(callback_query: CallbackQuery) -> None:
    context = cache_service.get_context_for_message(callback_query.message)
    fill = card_fill_service.get_fill_by_id(context['fill_id'])
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None,
        text=f'Трата {fill.amount} р. ({fill.description}) зафиксирована в {fill.fill_date}.'
    )


@dp.callback_query_handler(lambda cq: cq.data == 'scheduled_fill_callback_no')
async def scheduled_fill_callback_no(callback_query: CallbackQuery) -> None:
    context = cache_service.get_context_for_message(callback_query.message)
    fill = card_fill_service.get_fill_by_id(context['fill_id'])
    card_fill_service.delete_fill(fill)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None,
        text=f'Запись {fill.amount} р. ({fill.description}) в {fill.fill_date} удалена.'
    )


if __name__ == '__main__':
    start_app()
