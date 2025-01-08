from handlers.base import BaseMessageHandler, BaseCallbackHandler
from parsers.budget import BudgetMessage


class BudgetMessageHandler(BaseMessageHandler[BudgetMessage]):
    async def handle(self, message: BudgetMessage) -> None:
        scope = message.data
        cats_with_budget = self.card_fill_service.list_categories_with_budget(scope)
        await self.bot.send_message(
            chat_id=message.original_message.chat.id,
            text=str(cats_with_budget),
        )
