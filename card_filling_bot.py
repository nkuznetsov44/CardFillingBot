from typing import Optional, Type
from aiogram.types import Message
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
import asyncio

from app import App
from parsers import MessageParser, ParsedMessage
from parsers.month import MonthMessage, MonthMessageParser
from parsers.fill import (
    FillMessage,
    FillMessageParser,
    NetBalancesMessage,
    NetBalancesMessageParser,
)
from parsers.command import ServiceCommandMessage, ServiceCommandMessageParser
# from parsers.category import NewCategoryMessage, NewCategoryMessageParser
# from parsers.purchase_list import (
#     PurchaseMessage,
#     PurchaseMessageParser,
#     PurchaseListMessage,
#     PurchaseListParser,
#     DeletePurchaseMessage,
#     DeletePurchaseMessageParser,
# )
from handlers.base import BaseMessageHandler, BaseCallbackHandler
from handlers.fill import (
    FillMessageHandler,
    NetBalancesMessageHandler,
    ShowCategoryCallbackHandler,
    ChangeCategoryCallbackHandler,
    DeleteFillCallbackHandler,
)
from handlers.months import MonthsMessageHandler
from handlers.report import (
    MyFillsCurrentYearCallbackHandler,
    MyFillsPreviousYearCallbackHandler,
    PerMonthCurrentYearCallbackHandler,
    PerMonthPreviousYearCallbackHandler,
    PerYearCallbackHandler,
)
from handlers.command import ServiceCommandMessageHandler

# from handlers.category import (
#     handle_new_category_message,
#     handle_create_category,
#     handle_confirm_category,
# )
# from handlers.purchase import (
#     handle_delete_purchase_message,
#     handle_get_purchases_message,
#     handle_purchase_message,
# )


class CardFillingBot:
    message_handlers: dict[ParsedMessage, Type[BaseMessageHandler]] = {
        FillMessage: FillMessageHandler,
        MonthMessage: MonthsMessageHandler,
        NetBalancesMessage: NetBalancesMessageHandler,
        ServiceCommandMessage: ServiceCommandMessageHandler,
        # NewCategoryMessage: handle_new_category_message,
        # PurchaseMessage: handle_purchase_message,
        # PurchaseListMessage: handle_get_purchases_message,
        # DeletePurchaseMessage: handle_delete_purchase_message,
    }

    callback_handlers: list[Type[BaseCallbackHandler]] = [
        ShowCategoryCallbackHandler,
        ChangeCategoryCallbackHandler,
        DeleteFillCallbackHandler,
        MyFillsCurrentYearCallbackHandler,
        MyFillsPreviousYearCallbackHandler,
        PerMonthCurrentYearCallbackHandler,
        PerMonthPreviousYearCallbackHandler,
        PerYearCallbackHandler,
    ]

    def __init__(self, app: App) -> None:
        self.app = app
        self.message_parsers = self._init_message_parsers(self.app)
        self.app.dp.callback_query.middleware(CallbackAnswerMiddleware())
        self.app.dp.message()(self.message_handler)
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
            # NewCategoryMessageParser(app.cache_service),
            # DeletePurchaseMessageParser(),
            FillMessageParser(app.card_fill_service),
            MonthMessageParser(),
            # PurchaseMessageParser(app.card_fill_service),
            # PurchaseListParser(app.card_fill_service),
            NetBalancesMessageParser(app.card_fill_service),
            ServiceCommandMessageParser(),
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


# dp.register_callback_query_handler(
#     handle_create_category, Callback.NEW_CATEGORY.filter()
# )
# dp.register_callback_query_handler(
#     handle_confirm_category, Callback.CONFIRM_CATEGORY.filter()
# )


if __name__ == "__main__":
    app = App()
    bot = CardFillingBot(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start())
