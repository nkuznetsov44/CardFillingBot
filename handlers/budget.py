from handlers.base import BaseMessageHandler
from parsers.budget import BudgetMessage


class BudgetMessageHandler(BaseMessageHandler[BudgetMessage]):
    async def handle(self, message: BudgetMessage) -> None:
        scope = message.data
        budgets = self.card_fill_service.list_budgets(scope)
        
        def format_budget(b) -> str:
            limit_parts = []
            if b.monthly_limit:
                limit_parts.append(f'месяц: {b.monthly_limit:.0f}')
            if b.quarter_limit:
                limit_parts.append(f'квартал: {b.quarter_limit:.0f}')
            if b.year_limit:
                limit_parts.append(f'год: {b.year_limit:.0f}')
            limits = ', '.join(limit_parts) if limit_parts else 'не установлен'
            start_date_str = b.start_date.strftime('%m.%Y')
            return f'{b.category.name}: {limits} (с {start_date_str})'
        
        msg = '\n'.join(format_budget(b) for b in budgets)
        await self.bot.send_message(
            chat_id=message.original_message.chat.id,
            text=msg,
        )
