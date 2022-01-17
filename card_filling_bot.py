import logging
from typing import List, Tuple
from datetime import datetime
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from dto import Month, FillDto, CategoryDto, UserDto
from message_parsers import IParsedMessage
from message_parsers.month_message_parser import MonthMessageParser
from message_parsers.fill_message_parser import FillMessageParser
from message_parsers.new_category_message_parser import NewCategoryMessageParser
from message_formatters import (
    month_names, format_user_fills, format_monthly_report, format_yearly_report
)
from app import (
    dp, bot, card_fill_service, cache_service, graph_service, scheduler, start_app
)


logger = logging.getLogger(__name__)


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
        reply_text = f'Принято {fill.amount}р. от @{fill.user.username}'
        if fill.description:
            reply_text += f': {fill.description}'
        reply_text += f', категория: {fill.category.name}.'

        budget = card_fill_service.get_budget_for_category(fill.category, fill.scope)
        if budget:
            current_category_usage = card_fill_service.get_current_month_budget_usage_for_category(
                fill.category, fill.scope
            )
            reply_text += (
                f'\nИспользовано {current_category_usage.amount:.0f} из {current_category_usage.monthly_limit:.0f}.'
            )

        change_category_button = InlineKeyboardButton(text='Сменить категорию', callback_data='show_category')
        delete_fill_button = InlineKeyboardButton(text='Удалить пополнение', callback_data='delete_fill')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[change_category_button], [delete_fill_button]])
        sent_message = await bot.send_message(
            chat_id=parsed_message.original_message.chat.id,
            text=reply_text,
            reply_markup=keyboard
        )
        cache_service.set_fill_for_message(sent_message, fill)
    except:
        await bot.send_message(
            chat_id=parsed_message.original_message.chat.id,
            text='Ошибка добавления пополнения.'
        )
        logger.exception('Ошибка добавления пополнения')


async def handle_months_parsed_message(parsed_message: IParsedMessage[List[Month]]) -> None:
    months = parsed_message.data
    my = InlineKeyboardButton(text='Мои пополнения', callback_data='my')
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
                InlineKeyboardButton(text=cat.name, callback_data=f'change_category{cat.code}')
            )
        keyboard_buttons.append(buttons_group)
    keyboard_buttons.append([InlineKeyboardButton(
        text='СОЗДАТЬ НОВУЮ КАТЕГОРИЮ', callback_data='new_category')
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    reply_text = f'Выберите категорию для пополнения {fill.amount} р.'
    if fill.description:
        reply_text += f' ({fill.description})'
    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=reply_text,
        reply_markup=keyboard
    )
    cache_service.set_fill_for_message(sent_message, fill)


@dp.callback_query_handler(lambda cq: cq.data.startswith('change_category'))
async def change_category(callback_query: CallbackQuery) -> None:
    category_code = callback_query.data.replace('change_category', '')
    fill = cache_service.get_fill_for_message(callback_query.message)
    fill = card_fill_service.change_category_for_fill(fill.id, category_code)

    reply_text = f'Категория пополнения {fill.amount} р.'
    if fill.description:
        reply_text += f' ({fill.description})'
    reply_text += f' изменена на "{fill.category.name}".'

    budget = card_fill_service.get_budget_for_category(fill.category, fill.scope)
    if budget:
        current_category_usage = card_fill_service.get_current_month_budget_usage_for_category(
            fill.category, fill.scope
        )
        reply_text += (
            f'\nИспользовано {current_category_usage.amount:.0f} из {current_category_usage.monthly_limit:.0f}.'
        )

    change_category_button = InlineKeyboardButton(text='Сменить категорию', callback_data='show_category')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[change_category_button]])
    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=reply_text,
        reply_markup=keyboard
    )
    cache_service.set_fill_for_message(sent_message, fill)


@dp.callback_query_handler(lambda cq: cq.data == 'delete_fill')
async def delete_fill(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    card_fill_service.delete_fill(fill)
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=f'Пополнение {fill.amount} р. ({fill.description}) удалено.'
    )


@dp.callback_query_handler(lambda cq: cq.data == 'new_category')
async def create_new_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=(
            f'Создание категории для пополнения: {fill.amount} р. ({fill.description}).\n'
            'Ответом на это сообщение пришлите название, код и пропорцию для новой категории через запятую, '
            'например "Еда, FOOD, 0.8".'
        )
    )
    cache_service.set_fill_for_message(sent_message, fill)


@dp.callback_query_handler(lambda cq: cq.data == 'confirm_new_category')
async def confirm_new_category(callback_query: CallbackQuery) -> None:
    fill = cache_service.get_fill_for_message(callback_query.message)
    category = cache_service.get_category_for_message(callback_query.message)
    try:
        card_fill_service.create_new_category(category)
        fill = card_fill_service.change_category_for_fill(fill_id=fill.id, target_category_code=category.code)
        text = (
            f'Создана новая категория "{category.name}".\n'
            f'Категория пополнения {fill.amount} р.'
        )
        if fill.description:
            text += f' ({fill.description})'
        text += f' изменена на "{category.name}".'
    except:
        text = 'Ошибка создания категории.'
        logger.exception('Ошибка создания категории')
    await bot.send_message(chat_id=callback_query.message.chat.id, text=text)


@dp.callback_query_handler(lambda cq: cq.data == 'my')
async def my_fills_current_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    year = datetime.now().year
    from_user = UserDto.from_telegramapi(callback_query.from_user)
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    fills = card_fill_service.get_user_fills_in_months(from_user, months, year, scope)

    message_text = format_user_fills(fills, from_user, months, year)
    previous_year = InlineKeyboardButton(
        text='Предыдущий год', callback_data='fills_previous_year'
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[previous_year]])
    sent_message = await bot.send_message(
        chat_id=callback_query.message.chat.id, text=message_text, reply_markup=keyboard
    )
    cache_service.set_months_for_message(sent_message, months)


@dp.callback_query_handler(lambda cq: cq.data == 'fills_previous_year')
async def my_fills_previous_year(callback_query: CallbackQuery) -> None:
    months = cache_service.get_months_for_message(callback_query.message)
    previous_year = datetime.now().year - 1
    from_user = UserDto.from_telegramapi(callback_query.from_user)
    scope = card_fill_service.get_scope(callback_query.message.chat.id)
    fills = card_fill_service.get_user_fills_in_months(from_user, months, previous_year, scope)
    message_text = format_user_fills(fills, from_user, months, previous_year)
    await bot.send_message(chat_id=callback_query.message.chat.id, text=message_text)


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


if __name__ == '__main__':
    start_app()
