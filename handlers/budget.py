from typing import Any
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    Message
)
from handlers.base import BaseMessageHandler, BaseCallbackHandler
from services.state_service import BudgetEditState
from callbacks import Callback, EditBudgetCallback, BudgetPeriodCallback, BudgetConfirmCallback
from parsers.budget import BudgetMessage

class BudgetCommandHandler(BaseMessageHandler):
    async def handle(self, message: BudgetMessage) -> None:
        scope = self.card_fill_service.get_scope(message.original_message.chat.id)
        categories = self.card_fill_service.list_categories()
        budgets = {b.category.code: b for b in self.card_fill_service.list_budgets(scope)}
        
        # Create message text with budget details
        message_text = "Current budgets:\n\n"
        for category in categories:
            budget = budgets.get(category.code)
            budget_info = []
            if budget:
                if budget.monthly_limit:
                    budget_info.append(f"{budget.monthly_limit} per month")
                if budget.quarter_limit:
                    budget_info.append(f"{budget.quarter_limit} per quarter")
                if budget.year_limit:
                    budget_info.append(f"{budget.year_limit} per year")
            budget_text = " | ".join(budget_info) if budget_info else "No budget set"
            message_text += f"{category.get_emoji()} {category.name}: {budget_text}\n"
        message_text += "\nSelect category to edit budget:"
        
        # Create keyboard with simplified category buttons
        buttons = []
        for category in categories:
            callback_data = EditBudgetCallback(category_code=category.code).pack()
            button = InlineKeyboardButton(
                text=f"{category.get_emoji()} {category.name}",
                callback_data=callback_data
            )
            buttons.append([button])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await self.bot.send_message(
            chat_id=message.original_message.chat.id,
            text=message_text,
            reply_markup=keyboard
        )

class EditBudgetCallbackHandler(BaseCallbackHandler, callback=EditBudgetCallback):
    async def handle(self, callback: CallbackQuery, callback_data: EditBudgetCallback) -> None:
        category = self.card_fill_service.get_category(callback_data.category_code)
        scope = self.card_fill_service.get_scope(callback.message.chat.id)
        current_budget = self.card_fill_service.get_budget(category, scope)
        
        # Save category in state
        self.app.state_service.set_budget_edit_state(
            callback.message.chat.id,
            BudgetEditState.WAITING_FOR_AMOUNT,
            {"category_code": callback_data.category_code}
        )
        
        message_text = f"Category: {category.get_emoji()} {category.name}\n"
        if current_budget:
            budget_info = []
            if current_budget.monthly_limit:
                budget_info.append(f"{current_budget.monthly_limit} per month")
            if current_budget.quarter_limit:
                budget_info.append(f"{current_budget.quarter_limit} per quarter")
            if current_budget.year_limit:
                budget_info.append(f"{current_budget.year_limit} per year")
            if budget_info:
                message_text += f"Current budgets:\n" + "\n".join(budget_info) + "\n"
        message_text += "\nEnter new budget amount:"
        
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text
        )

class BudgetMessageHandler(BaseMessageHandler):
    async def handle(self, message: Message) -> None:
        state = self.app.state_service.get_budget_edit_state(message.chat.id)
        if not state:
            return
            
        current_state, data = state
        
        if current_state == BudgetEditState.WAITING_FOR_AMOUNT:
            try:
                amount = float(message.text)
                data["amount"] = amount
                
                # Ask for period
                self.app.state_service.set_budget_edit_state(
                    message.chat.id,
                    BudgetEditState.WAITING_FOR_PERIOD,
                    data
                )
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Monthly", callback_data=BudgetPeriodCallback(period="MONTH").pack())],
                    [InlineKeyboardButton(text="Quarterly", callback_data=BudgetPeriodCallback(period="QUARTER").pack())],
                    [InlineKeyboardButton(text="Yearly", callback_data=BudgetPeriodCallback(period="YEAR").pack())]
                ])
                
                category = self.card_fill_service.get_category(data["category_code"])
                await self.bot.send_message(
                    chat_id=message.chat.id,
                    text=f"New budget for {category.get_emoji()} {category.name}: {amount}\nSelect period:",
                    reply_markup=keyboard
                )
            except ValueError:
                await self.bot.send_message(
                    chat_id=message.chat.id,
                    text="Please enter a valid number"
                )

class BudgetPeriodCallbackHandler(BaseCallbackHandler, callback=BudgetPeriodCallback):
    async def handle(self, callback: CallbackQuery, callback_data: BudgetPeriodCallback) -> None:
        state, data = self.app.state_service.get_budget_edit_state(callback.message.chat.id)
        data["period"] = callback_data.period
        
        category = self.card_fill_service.get_category(data["category_code"])
        
        # Ask for confirmation
        self.app.state_service.set_budget_edit_state(
            callback.message.chat.id,
            BudgetEditState.WAITING_FOR_CONFIRMATION,
            data
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirm", 
                    callback_data=BudgetConfirmCallback(confirmed=True).pack()
                ),
                InlineKeyboardButton(
                    text="❌ Cancel", 
                    callback_data=BudgetConfirmCallback(confirmed=False).pack()
                )
            ]
        ])
        
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"Confirm new budget for {category.get_emoji()} {category.name}:\n"
                 f"Amount: {data['amount']}\n"
                 f"Period: {callback_data.period.lower()}",
            reply_markup=keyboard
        )

class BudgetConfirmCallbackHandler(BaseCallbackHandler, callback=BudgetConfirmCallback):
    async def handle(self, callback: CallbackQuery, callback_data: BudgetConfirmCallback) -> None:
        if not callback_data.confirmed:
            await self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="Budget edit cancelled"
            )
            self.app.state_service.clear_budget_edit_state(callback.message.chat.id)
            return
            
        state, data = self.app.state_service.get_budget_edit_state(callback.message.chat.id)
        scope = self.card_fill_service.get_scope(callback.message.chat.id)
        category = self.card_fill_service.get_category(data["category_code"])
        
        # Save budget to database
        budget = self.card_fill_service.update_budget(
            category=category,
            scope=scope,
            amount=data["amount"],
            period_type=data["period"]
        )
        
        # Format the success message with all limits
        budget_info = []
        if budget.monthly_limit:
            budget_info.append(f"{budget.monthly_limit} per month")
        if budget.quarter_limit:
            budget_info.append(f"{budget.quarter_limit} per quarter")
        if budget.year_limit:
            budget_info.append(f"{budget.year_limit} per year")
        
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"✅ Budget updated for {category.get_emoji()} {category.name}:\n" +
                 "\n".join(budget_info)
        )
        
        self.app.state_service.clear_budget_edit_state(callback.message.chat.id)
