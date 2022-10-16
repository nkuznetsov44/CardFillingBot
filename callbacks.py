from ast import Call
from enum import Enum, unique
from typing import Callable
from aiogram.types import CallbackQuery
from aiogram.utils.callback_data import CallbackData


@unique
class Callback(Enum):
    SHOW_CATEGORY = "show_category"
    CHANGE_CATEGORY = "change_category"
    DELETE_FILL = "delete_fill"
    NEW_CATEGORY = "new_category"
    CONFIRM_CATEGORY = "confirm_new_category"
    MY_FILLS = "my"
    MY_FILLS_PREVIOUS_YEAR = "fills_previous_year"
    MONTHLY_REPORT = "stat"
    MONTHLY_REPORT_PREVIOUS_YEAR = "previous_year"
    YEARLY_REPORT = "yearly_stat"
    SCHEDULE_FILL = "schedule_fill"
    SCHEDULE_MONTH = "schedule_month"
    SCHEDULE_DAY = "schedule_day"
    SCHEDULE_CONFIRM = "scheduled_fill_callback_yes"
    SCHEDULE_DECLINE = "scheduled_fill_callback_no"

    def filter(self) -> Callable[[CallbackQuery], bool]:
        return lambda cq: cq.data == self.value


change_category_cb = CallbackData(Callback.CHANGE_CATEGORY.value, "category_code")
schedule_month_cb = CallbackData(Callback.SCHEDULE_MONTH.value, "month")
schedule_day_cb = CallbackData(Callback.SCHEDULE_DAY.value, "month", "day")
