from enum import Enum, unique
from typing import Callable
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData


class EditBudgetCallback(CallbackData, prefix="edit_budget"):
    category_code: str


class BudgetPeriodCallback(CallbackData, prefix="budget_period"):
    period: str


class BudgetConfirmCallback(CallbackData, prefix="budget_confirm"):
    confirmed: bool


@unique
class Callback(Enum):
    SHOW_CATEGORY = "show_category"
    DELETE_FILL = "delete_fill"
    MY_FILLS = "my"
    MY_FILLS_PREVIOUS_YEAR = "fills_previous_year"
    MONTHLY_REPORT = "stat"
    MONTHLY_REPORT_PREVIOUS_YEAR = "previous_year"
    EDIT_BUDGET = "edit_budget"
    BUDGET_PERIOD = "budget_period"
    BUDGET_CONFIRM = "budget_confirm"

    def filter(self) -> Callable[[CallbackQuery], bool]:
        return lambda cq: cq.data == self.value


class ChangeCategoryCallback(CallbackData, prefix="change_category"):
    category_code: str
