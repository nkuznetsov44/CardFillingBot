from typing import Optional, Type
from aiogram.types import Message
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
import asyncio

from parsers import MessageParser, ParsedMessage
from parsers.month import MonthMessage, MonthMessageParser
from parsers.fill import (
    FillMessage,
    FillMessageParser,
    NetBalancesMessage,
    NetBalancesMessageParser,
)
from parsers.category import NewCategoryMessage, NewCategoryMessageParser
from parsers.purchase_list import (
    PurchaseMessage,
    PurchaseMessageParser,
    PurchaseListMessage,
    PurchaseListParser,
    DeletePurchaseMessage,
    DeletePurchaseMessageParser,
)

# from handlers.fill import (
#     handle_show_category,
#     handle_change_category,
#     handle_delete_fill,
# )
from handlers.base import BaseMessageHandler, BaseCallbackHandler
from handlers.fill import FillMessageHandler, NetBalancesMessageHandler, ShowCategoryCallbackHandler

# from handlers.months import handle_months_message
# from handlers.category import (
#     handle_new_category_message,
#     handle_create_category,
#     handle_confirm_category,
# )
# from handlers.report import (
#     handle_my_fills_current_year,
#     handle_my_fills_previous_year,
#     handle_per_month_current_year,
#     handle_per_month_previous_year,
#     handle_per_year,
# )
# from handlers.purchase import (
#     handle_delete_purchase_message,
#     handle_get_purchases_message,
#     handle_purchase_message,
# )

from callbacks import Callback

from app import App


class CardFillingBot:
    message_handlers: dict[ParsedMessage, Type[BaseMessageHandler]] = {
        FillMessage: FillMessageHandler,
        # MonthMessage: handle_months_message,
        # NewCategoryMessage: handle_new_category_message,
        # PurchaseMessage: handle_purchase_message,
        # PurchaseListMessage: handle_get_purchases_message,
        # DeletePurchaseMessage: handle_delete_purchase_message,
        NetBalancesMessage: NetBalancesMessageHandler,
    }

    callback_handlers: list[Type[BaseCallbackHandler]] = [
        ShowCategoryCallbackHandler,
    ]

    def __init__(self, app: App) -> None:
        self.app = app
        self.message_parsers = self._init_message_parsers(self.app)
        self.app.dp.message()(self.message_handler)
        self.app.dp.callback_query.middleware(CallbackAnswerMiddleware())
        self._register_callback_handlers(self.app)

    async def start(self) -> None:
        await self.app.start()

    @property
    def logger(self):
        return self.app.logger

    @property
    def bot(self):
        return self.app.bot

    @classmethod
    def _init_message_parsers(cls, app: App) -> list[MessageParser]:
        return [
            NewCategoryMessageParser(app.cache_service),
            DeletePurchaseMessageParser(),
            FillMessageParser(app.card_fill_service),
            MonthMessageParser(),
            PurchaseMessageParser(app.card_fill_service),
            PurchaseListParser(app.card_fill_service),
            NetBalancesMessageParser(app.card_fill_service),
        ]

    @classmethod
    def _register_callback_handlers(cls, app: App) -> None:
        for callback_handler_cls in cls.callback_handlers:
            app.dp.callback_query(callback_handler_cls.callback_filter)(callback_handler_cls(app).handle)

    async def fallback_handler(self, message: Message) -> None:
        self.logger.warning(f'Fallback to default handler for message "{message.text}"')
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=(
                'Укажите сумму и комментарий в сообщении, например: "150 макдак", для добавления новой записи, '
                'или один или несколько месяцев, например, "январь февраль", для просмотра статистики.'
            ),
        )

    async def error_handler(self, message: Message) -> None:
        await self.bot.send_message(
            chat_id=message.chat.id, text="Произошла ошибка обработки. Попробуйте позже."
        )

    async def message_handler(self, message: Message) -> None:
        self.logger.info(f"Received message {message.text}")
        for parser in self.message_parsers:
            parsed_message: Optional[ParsedMessage] = None
            try:
                parsed_message = parser.parse(message)
            except:
                self.logger.exception(f"Parser {parser} failed")

            if parsed_message:
                self.logger.info(f"Handling message {parsed_message}")
                handler_cls = self.message_handlers[type(parsed_message)]
                try:
                    await handler_cls(app).handle(parsed_message)
                    # await handler(parsed_message)
                except:
                    self.logger.exception(f"Handler {handler_cls} failed")
                    await self.error_handler(message)
                finally:
                    return

        await self.fallback_handler(message)


"""
dp.register_callback_query_handler(
    handle_show_category, Callback.SHOW_CATEGORY.filter()
)
dp.register_callback_query_handler(handle_change_category, Callback.CHANGE_CATEGORY.filter())
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
dp.register_callback_query_handler(
    handle_scheduled_fill_confirm, Callback.SCHEDULE_CONFIRM.filter()
)
dp.register_callback_query_handler(
    handle_scheduled_fill_declined, Callback.SCHEDULE_DECLINE.filter()
)
"""


if __name__ == "__main__":
    app = App()
    bot = CardFillingBot(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start())
