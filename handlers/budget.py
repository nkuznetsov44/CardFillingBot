from handlers.base import BaseMessageHandler
from parsers.budget import BudgetMessage


class BudgetMessageHandler(BaseMessageHandler[BudgetMessage]):
    async def handle(self, message: BudgetMessage) -> None:
        scope = message.data
        budgets = self.card_fill_service.list_budgets(scope)
        msg = '\n'.join(f'{b.category.name}: {b.monthly_limit}' for b in budgets)
        await self.bot.send_message(
            chat_id=message.original_message.chat.id,
            text=msg,
        )
