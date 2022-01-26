from typing import List, Dict, Optional
from datetime import datetime
from dto import (
    Month, FillDto, UserDto, FillScopeDto, UserSumOverPeriodDto, CategorySumOverPeriodDto,
    ProportionOverPeriodDto, SummaryOverPeriodDto, BudgetDto
)


month_names = {
    Month.january: 'Январь',
    Month.february: 'Февраль',
    Month.march: 'Март',
    Month.april: 'Апрель',
    Month.may: 'Май',
    Month.june: 'Июнь',
    Month.july: 'Июль',
    Month.august: 'Август',
    Month.september: 'Сентябрь',
    Month.october: 'Октябрь',
    Month.november: 'Ноябрь',
    Month.december: 'Декабрь'
}


def format_user_fills(fills: List[FillDto], from_user: UserDto, months: List[Month], year: int) -> str:
    """Example message:
        Пополения @username за Январь, Февраль 2021:
        2022-01-09 09:06:09: 50.0 мобильная связь регулярные
        2022-02-02 11:23:15: 120.0 бар рестораны

    """
    m_names = ', '.join(map(month_names.get, months))
    if len(fills) == 0:
        text = f'Не было трат в {m_names} {year}.'
    else:
        text = (
            f'Траты @{from_user.username} за {m_names} {year}:\n' +
            '\n'.join(
                [f'{fill.fill_date}: {fill.amount} {fill.description} {fill.category.name}' for fill in fills]
            )
        )
    return text


def format_by_user_block(data: List[UserSumOverPeriodDto], scope: FillScopeDto) -> str:
    if scope.scope_type == 'PRIVATE':
        return '\n'.join([f'{user_sum.amount:.0f}' for user_sum in data])
    return (
        '\n'.join([f'@{user_sum.username}: {user_sum.amount:.0f}' for user_sum in data])
        .replace('_', '\\_')
    )


def format_by_category_block(data: List[CategorySumOverPeriodDto], display_limits: bool) -> str:
    rows = []
    for category_sum in data:
        text = f'  - {category_sum.category_name}: {category_sum.amount:.0f}'
        if display_limits and category_sum.monthly_limit:
            text += f' (из {category_sum.monthly_limit:.0f})'
        rows.append(text)
    return '_Категории:_\n' + '\n'.join(rows)


def format_proportions_block(data: ProportionOverPeriodDto) -> str:
    return (
        f'_Пропорции:_\n  - текущая: {data.proportion_actual:.2f}\n'
        f'  - ожидаемая: {data.proportion_target:.2f}'
    ).replace('.', '\\.')


def format_monthly_report(data: Dict[Month, SummaryOverPeriodDto], year: int, scope: FillScopeDto) -> str:
    """Example message:
        Январь 2022:
        @username1: 12300
        @username2: 16120

        Категории:
          - для дома: 5726
          - рестораны: 3000

        Пропорции:
          - текущая: 0.86
          - ожидаемая: 0.88
    """
    message_text = ''
    for month, data_month in data.items():
        message_text += f'*{month_names[month]} {year}:*\n'
        message_text += format_by_user_block(data_month.by_user, scope) + '\n\n'
        message_text += format_by_category_block(data_month.by_category, display_limits=True)
        if scope.scope_type == 'GROUP':
            message_text += '\n\n' + format_proportions_block(data_month.proportions)
        message_text += '\n\n'
    return (
        message_text
        .replace('-', '\\-')
        .replace('(', '\\(')
        .replace(')', '\\)')
    )


def format_yearly_report(data: SummaryOverPeriodDto, year: int, scope: FillScopeDto) -> str:
    """Example message:
        За 2022 год:
        @username1: 12300
        @username2: 16120

        Категории:
          - для дома: 5726
          - рестораны: 3000

        Пропорции:
          - текущая: 0.86
          - ожидаемая: 0.88
    """
    caption = f'*За {year} год:*\n'
    caption += format_by_user_block(data.by_user, scope) + '\n\n'
    caption += format_by_category_block(data.by_category, display_limits=False)
    if scope.scope_type == 'GROUP':
        caption += '\n\n' + format_proportions_block(data.proportions)
    return caption.replace('-', '\\-')


def get_current_month_name() -> str:
    current_month = Month(datetime.now().month)
    return month_names[current_month]


def format_fill_confirmed(
    fill: FillDto, budget: Optional[BudgetDto], current_category_usage: Optional[float]
) -> str:
    reply_text = f'Принято {fill.amount}р. от @{fill.user.username}'
    if fill.description:
        reply_text += f': {fill.description}'
    reply_text += f', категория: {fill.category.name}.'
    if budget:
        reply_text += (
            f'\nИспользовано {current_category_usage.amount:.0f} из {current_category_usage.monthly_limit:.0f}.'
        )
    return reply_text
