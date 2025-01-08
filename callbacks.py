from enum import Enum, unique
from typing import Callable
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData


@unique
class Callback(Enum):
    SHOW_CATEGORY = "show_category"
    DELETE_FILL = "delete_fill"
    MY_FILLS = "my"
    MY_FILLS_PREVIOUS_YEAR = "fills_previous_year"
    MONTHLY_REPORT = "stat"
    MONTHLY_REPORT_PREVIOUS_YEAR = "previous_year"
    YEARLY_REPORT = "yearly_stat"

    def filter(self) -> Callable[[CallbackQuery], bool]:
        return lambda cq: cq.data == self.value


class ChangeCategoryCallback(CallbackData, prefix="change_category"):
    category_code: str
