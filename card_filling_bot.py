import logging
from typing import Callable
from aiogram.types import Message

from parsers import MessageParser, ParsedMessage
from parsers.month import MonthMessage, MonthMessageParser
from parsers.fill import FillMessage, FillMessageParser
from parsers.category import NewCategoryMessage, NewCategoryMessageParser
from parsers.purchase_list import (
    PurchaseMessage,
    PurchaseMessageParser,
    PurchaseListMessage,
    PurchaseListParser,
    DeletePurchaseMessage,
    DeletePurchaseMessageParser,
)

from handlers.fill import (
    handle_fill_message,
    handle_show_category,
    handle_change_category,
    handle_delete_fill,
)
from handlers.months import handle_months_message
from handlers.category import (
    handle_new_category_message,
    handle_create_category,
    handle_confirm_category,
)
from handlers.report import (
    handle_my_fills_current_year,
    handle_my_fills_previous_year,
    handle_per_month_current_year,
    handle_per_month_previous_year,
    handle_per_year,
)
from handlers.purchase import (
    handle_delete_purchase_message,
    handle_get_purchases_message,
    handle_purchase_message,
)
from handlers.schedule import (
    handle_schedule_day,
    handle_schedule_fill,
    handle_schedule_month,
    handle_scheduled_fill_confirm,
    handle_scheduled_fill_declined,
)

from callbacks import Callback, change_category_cb, schedule_day_cb, schedule_month_cb

from app import dp, bot, card_fill_service, cache_service, start_app


logger = logging.getLogger(__name__)


message_parsers: list[MessageParser] = [
    NewCategoryMessageParser(cache_service),
    DeletePurchaseMessageParser(),
    FillMessageParser(card_fill_service),
    MonthMessageParser(),
    PurchaseMessageParser(card_fill_service),
    PurchaseListParser(card_fill_service),
]


message_handlers: dict[ParsedMessage, Callable[[ParsedMessage], None]] = {
    FillMessage: handle_fill_message,
    MonthMessage: handle_months_message,
    NewCategoryMessage: handle_new_category_message,
    PurchaseMessage: handle_purchase_message,
    PurchaseListMessage: handle_get_purchases_message,
    DeletePurchaseMessage: handle_delete_purchase_message,
}


async def fallback_handler(message: Message) -> None:
    logger.warning(f'Fallback to default handler for message "{message.text}"')
    await bot.send_message(
        chat_id=message.chat.id,
        text=(
            'Укажите сумму и комментарий в сообщении, например: "150 макдак", для добавления новой записи, '
            'или один или несколько месяцев, например, "январь февраль", для просмотра статистики.'
        ),
    )


async def error_handler(message: Message) -> None:
    await bot.send_message(
        chat_id=message.chat.id, text="Произошла ошибка обработки. Попробуйте позже."
    )


@dp.message_handler()
async def message_handler(message: Message) -> None:
    logger.info(f"Received message {message.text}")
    for parser in message_parsers:
        parsed_message = parser.parse(message)
        if parsed_message:
            logger.info(f"Handling message {parsed_message.__name__}")
            handler = message_handlers[type(parsed_message)]
            try:
                await handler(parsed_message)
            except:
                logger.exception(f"Handler {handler.__name__} failed")
                await error_handler(message)
            finally:
                return

    await fallback_handler(message)


dp.register_callback_query_handler(
    handle_show_category, Callback.SHOW_CATEGORY.filter()
)
dp.register_callback_query_handler(handle_change_category, change_category_cb.filter())
dp.register_callback_query_handler(handle_delete_fill, Callback.DELETE_FILL.filter())
dp.register_callback_query_handler(
    handle_create_category, Callback.NEW_CATEGORY.filter()
)
dp.register_callback_query_handler(
    handle_confirm_category, Callback.CONFIRM_CATEGORY.filter()
)
dp.register_callback_query_handler(
    handle_my_fills_current_year, Callback.MY_FILLS.filter()
)
dp.register_callback_query_handler(
    handle_my_fills_previous_year, Callback.MY_FILLS_PREVIOUS_YEAR.filter()
)
dp.register_callback_query_handler(
    handle_per_month_current_year, Callback.MONTHLY_REPORT.filter()
)
dp.register_callback_query_handler(
    handle_per_month_previous_year, Callback.MONTHLY_REPORT_PREVIOUS_YEAR.filter()
)
dp.register_callback_query_handler(handle_per_year, Callback.YEARLY_REPORT.filter())
dp.register_callback_query_handler(
    handle_schedule_fill, Callback.SCHEDULE_FILL.filter()
)
dp.register_callback_query_handler(handle_schedule_month, schedule_month_cb.filter())
dp.register_callback_query_handler(handle_schedule_day, schedule_day_cb.filter())
dp.register_callback_query_handler(
    handle_scheduled_fill_confirm, Callback.SCHEDULE_CONFIRM.filter()
)
dp.register_callback_query_handler(
    handle_scheduled_fill_declined, Callback.SCHEDULE_DECLINE.filter()
)


if __name__ == "__main__":
    start_app()
