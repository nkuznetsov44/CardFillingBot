from typing import Optional
from dataclasses import dataclass
import prettytable
from emoji import emojize
from entities import (
    Month,
    Fill,
    User,
    FillScope,
    UserSumOverPeriod,
    CategorySumOverPeriod,
    SummaryOverPeriod,
    Budget,
    UserSumOverPeriodWithBalance,
    Income,
)


month_names = {
    Month.january: "Январь",
    Month.february: "Февраль",
    Month.march: "Март",
    Month.april: "Апрель",
    Month.may: "Май",
    Month.june: "Июнь",
    Month.july: "Июль",
    Month.august: "Август",
    Month.september: "Сентябрь",
    Month.october: "Октябрь",
    Month.november: "Ноябрь",
    Month.december: "Декабрь",
}


BASE_CURRENCY_ALIAS = 'дин'
CAT_EMOJI_FIELD_NAME = emojize(":card_index_dividers:")
STATISTICS_FIELD_NAME = emojize(':bar_chart:')
RED_CROSS = emojize(':cross_mark:')
GREEN_TICK = emojize(':check_mark_button:')


def get_max_table_desc_width(scope_type: str):
    if scope_type == "PRIVATE":
        return 17
    return 13


def get_max_income_table_desc_width(scope_type: str):
    """Get description column width for income tables, accounting for wider amount column"""
    if scope_type == "PRIVATE":
        return 15  # 17 - 2 (7-5 difference in amount column width)
    return 11      # 13 - 2 (7-5 difference in amount column width)


def format_fills_list_as_table(fills: list[Fill], scope: FillScope) -> str:
    tbl = prettytable.PrettyTable()
    tbl._max_width = {
        "Дата": 5,
        "Сумма": 5,
        CAT_EMOJI_FIELD_NAME: 1,
        "Описание": get_max_table_desc_width(scope.scope_type),
    }
    tbl.border = False
    tbl.hrules = prettytable.HEADER
    tbl.left_padding_width = 0
    tbl.right_padding_width = 1
    tbl.field_names = ["Дата", "Сумма", CAT_EMOJI_FIELD_NAME, "Описание"]
    tbl.align["Дата"] = "r"
    tbl.align["Сумма"] = "r"
    tbl.align["Описание"] = "l"
    tbl.align["C"] = "l"
    for fill in fills:
        tbl.add_row(
            [
                fill.fill_date.strftime("%d/%m"),
                f"{fill.amount:.0f}",
                fill.category.get_emoji(),
                fill.description,
            ]
        )
    return tbl.get_string()


def format_user_fills(
    fills: list[Fill],
    from_user: User,
    months: list[Month],
    year: int,
    scope: FillScope,
) -> str:
    m_names = ", ".join(map(month_names.get, months))
    if len(fills) == 0:
        text = f"Не было трат в {m_names} {year}."
    else:
        fills_table = format_fills_list_as_table(fills, scope)
        text = (
            f"Траты @{from_user.username} за {m_names} {year}:\n"
            + "```"
            + fills_table
            + "```"
        )
    text = text.replace("-", "\\-").replace("_", "\\_").replace(".", "\\.")
    return text


def format_by_user_block(data: list[UserSumOverPeriod], scope: FillScope) -> str:
    if scope.scope_type == "PRIVATE":
        return "\n".join([f"{user_sum.amount:.0f}" for user_sum in data])
    else:
        result = "\n".join(
            [f"@{user_sum.user.username}: {user_sum.amount:.0f}" for user_sum in data]
        )
        result += f"\nВсего: {sum(user_sum.amount for user_sum in data):.0f}"
        return result.replace("_", "\\_")


def format_by_user_balance_block(
    data: list[UserSumOverPeriodWithBalance], scope: FillScope
) -> str:
    if scope.scope_type == "PRIVATE":
        raise NotImplementedError
    return "\n".join(
        [
            f"@{user_sum.user.username}: {user_sum.amount:.0f}\n    баланс: {user_sum.balance:.0f}"
            for user_sum in data
        ]
    ).replace("_", "\\_")


@dataclass(frozen=True)
class CategoryTableRowData:
    emoji: str
    name: str
    usage: float
    limit: float


def category_with_limits_table(data: list[CategoryTableRowData], header: str, need_usage_emoji: bool = True) -> str:
    if not data:
        return ''

    tbl = prettytable.PrettyTable()
    tbl._max_width = {
        CAT_EMOJI_FIELD_NAME: 1,
        "Категория": 11,
        "Usage": 7,
        "Лимит": 7,
        STATISTICS_FIELD_NAME: 1,
    }

    tbl.border = False
    tbl.hrules = prettytable.HEADER
    tbl.left_padding_width = 0
    tbl.right_padding_width = 1
    tbl.field_names = [CAT_EMOJI_FIELD_NAME, "Категория", "Usage", "Лимит", STATISTICS_FIELD_NAME]
    tbl.align["Категория"] = "l"
    tbl.align["Usage"] = "r"
    tbl.align["Лимит"] = "r"

    def _fmt_usage(usage: float, limit: Optional[float]) -> str:
        if not limit:
            return '-'
        if usage <= limit:
            return GREEN_TICK
        return RED_CROSS

    for r in data:
        tbl.add_row([
            r.emoji,
            r.name,
            f'{r.usage:.0f}',
            f'{r.limit:.0f}' if r.limit else '-',
            _fmt_usage(r.usage, r.limit),
        ])

    return f'```{header}\n{tbl.get_string()}```'


def format_by_category_block(data: list[CategorySumOverPeriod]) -> str:
    monthly_table_data: list[CategoryTableRowData] = []
    quarter_table_data: list[CategoryTableRowData] = []
    year_table_data: list[CategoryTableRowData] = []
    for category_sum in data:
        emoji = category_sum.category.get_emoji()
        name = category_sum.category.name
        if category_sum.amount > 0:
            monthly_table_data.append(
                CategoryTableRowData(
                    emoji=emoji,
                    name=name,
                    usage=category_sum.amount,
                    limit=category_sum.monthly_limit,
                )
            )
        if category_sum.quarter_limit:
            quarter_table_data.append(
                CategoryTableRowData(
                    emoji=emoji,
                    name=name,
                    usage=category_sum.quarter_amount,
                    limit=category_sum.quarter_limit,
                )
            )
        if category_sum.year_limit:
            year_table_data.append(
                CategoryTableRowData(
                    emoji=emoji,
                    name=name,
                    usage=category_sum.year_amount,
                    limit=category_sum.year_limit,
                )
            )

    monthly_table_data.sort(key=lambda row: row.usage, reverse=True)
    quarter_table_data.sort(key=lambda row: row.usage, reverse=True)
    year_table_data.sort(key=lambda row: row.usage, reverse=True)

    monthly_tbl = category_with_limits_table(data=monthly_table_data, header='Месяц')
    quarter_tbl = category_with_limits_table(data=quarter_table_data, header='Квартал')
    year_tbl = category_with_limits_table(data=year_table_data, header='Год')

    return '\n\n'.join([monthly_tbl, quarter_tbl, year_tbl])


def format_monthly_report(
    data: dict[Month, SummaryOverPeriod], 
    year: int, 
    scope: FillScope,
    income_data: Optional[dict[Month, list[UserSumOverPeriod]]] = None
) -> str:
    message_text = ""
    for month, data_month in data.items():
        message_text += f"*{month_names[month]} {year}:*\n"
        
        # Add income section if available
        if income_data and month in income_data and income_data[month]:
            message_text += "*Доходы:*\n"
            message_text += format_by_user_income_block(income_data[month], scope) + "\n\n"
        
        # Add expenses section
        message_text += "*Расходы:*\n"
        message_text += format_by_user_block(data_month.by_user, scope) + "\n\n"
        message_text += format_by_category_block(data_month.by_category)
        message_text += "\n\n"
    return message_text.replace("-", "\\-").replace("(", "\\(").replace(")", "\\)").replace(".", "\\.")


def format_monthly_report_group(
    data: dict[Month, list[UserSumOverPeriodWithBalance]],
    year: int,
    scope: FillScope,
) -> str:
    message_text = ""
    for month, data_month in data.items():
        message_text += f"*{month_names[month]} {year}:*\n"
        message_text += format_by_user_balance_block(data_month, scope) + "\n\n"
    return message_text.replace("-", "\\-").replace("(", "\\(").replace(")", "\\)")


def format_fill_confirmed(
    fill: Fill, budget: Optional[Budget], current_category_usage: Optional[float]
) -> str:
    reply_text = f"Принято {fill.amount} {BASE_CURRENCY_ALIAS}. от @{fill.user.username}"
    if fill.description:
        reply_text += f": {fill.description}"
    reply_text += f", категория: {fill.category.get_emoji()} {fill.category.name}."
    limit = None
    if budget:
        limit = budget.monthly_limit or budget.quarter_limit or budget.year_limit
        if limit:
            reply_text += f"\nИспользовано {current_category_usage.amount:.0f} из {limit:.0f}."
    return reply_text


def format_income_confirmed(income: Income) -> str:
    reply_text = f"Доход {income.amount} {BASE_CURRENCY_ALIAS}. от @{income.user.username}"
    if income.description:
        reply_text += f": {income.description}"
    
    # Show original currency if different from base
    if income.original_currency and income.original_amount != income.amount:
        reply_text += f"\n(Оригинал: {income.original_amount} {income.original_currency.value})"
    
    return reply_text


def format_income_list_as_table(incomes: list[Income], scope: FillScope) -> str:
    tbl = prettytable.PrettyTable()
    tbl._max_width = {
        "Дата": 5,
        "Сумма": 7,
        "Описание": get_max_income_table_desc_width(scope.scope_type),
    }
    tbl.border = False
    tbl.hrules = prettytable.HEADER
    tbl.left_padding_width = 0
    tbl.right_padding_width = 1
    tbl.field_names = ["Дата", "Сумма", "Описание"]
    tbl.align["Дата"] = "r"
    tbl.align["Сумма"] = "r"
    tbl.align["Описание"] = "l"
    for income in incomes:
        tbl.add_row(
            [
                income.income_date.strftime("%d/%m"),
                f"{income.amount:.0f}",
                income.description or "",
            ]
        )
    return tbl.get_string()


def format_user_income(
    incomes: list[Income],
    from_user: User,
    months: list[Month],
    year: int,
    scope: FillScope,
) -> str:
    m_names = ", ".join(map(month_names.get, months))
    if len(incomes) == 0:
        text = f"Не было доходов в {m_names} {year}."
    else:
        income_table = format_income_list_as_table(incomes, scope)
        text = (
            f"Доходы @{from_user.username} за {m_names} {year}:\n"
            + "```"
            + income_table
            + "```"
        )
    text = text.replace("-", "\\-").replace("_", "\\_").replace(".", "\\.")
    return text


def format_by_user_income_block(data: list[UserSumOverPeriod], scope: FillScope) -> str:
    if scope.scope_type == "PRIVATE":
        return "\n".join([f"{user_sum.amount:.0f}" for user_sum in data])
    else:
        result = "\n".join(
            [f"@{user_sum.user.username}: {user_sum.amount:.0f}" for user_sum in data]
        )
        result += f"\nВсего доходов: {sum(user_sum.amount for user_sum in data):.0f}"
        return result.replace("_", "\\_")
