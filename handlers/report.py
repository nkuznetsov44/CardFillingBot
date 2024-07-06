from uuid import uuid4
from datetime import datetime
from typing import Any
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BufferedInputFile,
)
from handlers.base import BaseCallbackHandler
from formatters import (
    month_names,
    format_user_fills,
    format_monthly_report,
    format_monthly_report_group,
    format_yearly_report,
)
from entities import User, FillScope
from settings import settings
from callbacks import Callback


class MyFillsCurrentYearCallbackHandler(BaseCallbackHandler, callback=Callback.MY_FILLS):
    async def handle(self, callback: CallbackQuery, callback_data: Any | None = None) -> None:
        months = self.cache_service.get_months_for_message(callback.message)
        year = datetime.now().year
        from_user = User.from_telegramapi(callback.from_user)
        scope = self.card_fill_service.get_scope(callback.message.chat.id)
        fills = self.card_fill_service.get_user_fills_in_months(from_user, months, year, scope)

        message_text = format_user_fills(fills, from_user, months, year, scope)
        previous_year = InlineKeyboardButton(
            text="Предыдущий год",
            callback_data=Callback.MY_FILLS_PREVIOUS_YEAR.value,
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[previous_year]])
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )


class MyFillsPreviousYearCallbackHandler(BaseCallbackHandler, callback=Callback.MY_FILLS_PREVIOUS_YEAR):
    async def handle(self, callback: CallbackQuery, callback_data: Any | None = None) -> None:
        months = self.cache_service.get_months_for_message(callback.message)
        previous_year = datetime.now().year - 1
        from_user = User.from_telegramapi(callback.from_user)
        scope = self.card_fill_service.get_scope(callback.message.chat.id)
        fills = self.card_fill_service.get_user_fills_in_months(
            from_user, months, previous_year, scope
        )
        message_text = format_user_fills(fills, from_user, months, previous_year, scope)
        await self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
        )


class PerMonthCurrentYearCallbackHandler(BaseCallbackHandler, callback=Callback.MONTHLY_REPORT):
    async def handle(self, callback: CallbackQuery, callback_data: Any | None = None) -> None:
        scope = self.card_fill_service.get_scope(callback.message.chat.id)
        if scope.scope_id == settings.pay_silivri_scope_id:
            return await self._per_month_silivri(callback, scope)
        return await self._per_month_default(callback, scope)

    async def _per_month_silivri(self, callback: CallbackQuery, scope: FillScope) -> None:
        months = self.cache_service.get_months_for_message(callback.message)
        year = datetime.now().year
        data = self.card_fill_service.get_debt_monthly_report_by_user(months, year, scope)

        message_text = format_monthly_report_group(data, year, scope)
        if len(months) == 1:
            month = months[0]
            diagram = self.graph_service.create_by_user_diagram(
                data[month], name=f"{month_names[month]} {year}"
            )
            if diagram:
                await self.bot.send_photo(
                    callback.message.chat.id,
                    photo=BufferedInputFile(file=diagram, filename=str(uuid4())),
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
            else:
                await self.bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=message_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                )

    async def _per_month_default(self, callback: CallbackQuery, scope: FillScope) -> None:
        months = self.cache_service.get_months_for_message(callback.message)
        year = datetime.now().year
        data = self.card_fill_service.get_monthly_report(months, year, scope)

        message_text = format_monthly_report(data, year, scope)
        previous_year = InlineKeyboardButton(
            text="Предыдущий год", callback_data=Callback.MONTHLY_REPORT_PREVIOUS_YEAR.value
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[previous_year]])

        if len(months) == 1:
            month = months[0]
            diagram = self.graph_service.create_by_category_diagram(
                data[month].by_category, name=f"{month_names[month]} {year}"
            )
            if diagram:
                sent_message = await self.bot.send_photo(
                    callback.message.chat.id,
                    photo=BufferedInputFile(file=diagram, filename=str(uuid4())),
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=keyboard,
                )
                self.cache_service.set_months_for_message(sent_message, months)
                return

        sent_message = await self.bot.send_message(
            chat_id=callback.message.chat.id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboard,
        )
        self.cache_service.set_months_for_message(sent_message, months)


class PerMonthPreviousYearCallbackHandler(BaseCallbackHandler, callback=Callback.MONTHLY_REPORT_PREVIOUS_YEAR):
    async def handle(self, callback: CallbackQuery, callback_data: Any | None = None) -> None:
        months = self.cache_service.get_months_for_message(callback.message)
        previous_year = datetime.now().year - 1
        scope = self.card_fill_service.get_scope(callback.message.chat.id)
        data = self.card_fill_service.get_monthly_report(months, previous_year, scope)

        message_text = format_monthly_report(data, previous_year, scope)
        if len(months) == 1:
            month = months[0]
            diagram = self.graph_service.create_by_category_diagram(
                data[month].by_category, name=f"{month_names[month]} {previous_year}"
            )
            if diagram:
                sent_message = await self.bot.send_photo(
                    callback.message.chat.id,
                    photo=BufferedInputFile(file=diagram, filename=str(uuid4())),
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
                self.cache_service.set_months_for_message(sent_message, months)
                return

        sent_message = await self.bot.send_message(
            chat_id=callback.message.chat.id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        self.cache_service.set_months_for_message(sent_message, months)


class PerYearCallbackHandler(BaseCallbackHandler, callback=Callback.YEARLY_REPORT):
    async def handle(self, callback: CallbackQuery, callback_data: Any | None = None) -> None:
        year = datetime.now().year
        scope = self.card_fill_service.get_scope(callback.message.chat.id)
        data = self.card_fill_service.get_yearly_report(year, scope)
        diagram = self.graph_service.create_by_category_diagram(data.by_category, name=str(year))
        caption = format_yearly_report(data, year, scope)
        await self.bot.send_photo(
            callback.message.chat.id,
            photo=BufferedInputFile(file=diagram, filename=str(uuid4())),
            caption=caption,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
