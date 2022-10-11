from typing import List, Dict, Optional
import prettytable
from emoji import emojize
from dto import (
    Month, FillDto, UserDto, FillScopeDto, UserSumOverPeriodDto, CategorySumOverPeriodDto,
    ProportionOverPeriodDto, SummaryOverPeriodDto, BudgetDto, UserSumOverPeriodWithBalanceDto,
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


def format_fills_list_as_table(fills: List[FillDto], scope: FillScopeDto) -> str:
    if scope.scope_type == 'PRIVATE':
        max_desc_width = 17
    else:
        max_desc_width = 13
    tbl = prettytable.PrettyTable()
    cat_emoji_field_name = emojize(':card_index_dividers:')
    tbl._max_width = {'Дата': 5, "Сумма": 5, cat_emoji_field_name: 1, 'Описание': max_desc_width}
    tbl.border = False
    tbl.hrules = prettytable.HEADER
    tbl.left_padding_width = 0
    tbl.right_padding_width = 1
    tbl.field_names = ['Дата', 'Сумма', cat_emoji_field_name, 'Описание']
    tbl.align['Дата'] = 'r'
    tbl.align['Сумма'] = 'r'
    tbl.align['Описание'] = 'l'
    tbl.align['C'] = 'l'
    for fill in fills:
        tbl.add_row([
            fill.fill_date.strftime('%d/%m'),
            f'{fill.amount:.0f}',
            fill.category.get_emoji(),
            fill.description,
        ])
    return tbl.get_string()


def format_user_fills(
    fills: List[FillDto],
    from_user: UserDto,
    months: List[Month],
    year: int,
    scope: FillScopeDto
) -> str:
    m_names = ', '.join(map(month_names.get, months))
    if len(fills) == 0:
        text = f'Не было трат в {m_names} {year}.'
    else:
        fills_table = format_fills_list_as_table(fills, scope)
        text = (
            f'Траты @{from_user.username} за {m_names} {year}:\n' +
            '```' + fills_table + '```'
        )
    text = text.replace('-', '\\-').replace('_', '\\_').replace('.', '\\.')
    return text


def format_by_user_block(data: List[UserSumOverPeriodDto], scope: FillScopeDto) -> str:
    if scope.scope_type == 'PRIVATE':
        return '\n'.join([f'{user_sum.amount:.0f}' for user_sum in data])
    return (
        '\n'.join([f'@{user_sum.user.username}: {user_sum.amount:.0f}' for user_sum in data])
        .replace('_', '\\_')
    )


def format_by_user_balance_block(data: List[UserSumOverPeriodWithBalanceDto], scope: FillScopeDto) -> str:
    if scope.scope_type == 'PRIVATE':
        raise NotImplementedError
    return (
        '\n'.join([f'@{user_sum.user.username}: {user_sum.amount:.0f}\n    баланс: {user_sum.balance}' for user_sum in data])
        .replace('_', '\\_')
    )


def format_by_category_block(data: List[CategorySumOverPeriodDto], display_limits: bool) -> str:
    rows = []
    for category_sum in data:
        text = f'  - {category_sum.category.get_emoji()} {category_sum.category.name}: {category_sum.amount:.0f}'
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


def format_monthly_report_group(
    data: Dict[Month, List[UserSumOverPeriodWithBalanceDto]], year: int, scope: FillScopeDto
) -> str:
    message_text = ''
    for month, data_month in data.items():
        message_text += f'*{month_names[month]} {year}:*\n'
        message_text += format_by_user_balance_block(data_month, scope) + '\n\n'
    return (
        message_text
        .replace('-', '\\-')
        .replace('(', '\\(')
        .replace(')', '\\)')
    )


def format_yearly_report(data: SummaryOverPeriodDto, year: int, scope: FillScopeDto) -> str:
    caption = f'*За {year} год:*\n'
    caption += format_by_user_block(data.by_user, scope) + '\n\n'
    caption += format_by_category_block(data.by_category, display_limits=False)
    if scope.scope_type == 'GROUP':
        caption += '\n\n' + format_proportions_block(data.proportions)
    return caption.replace('-', '\\-')


def format_fill_confirmed(
    fill: FillDto, budget: Optional[BudgetDto], current_category_usage: Optional[float]
) -> str:
    reply_text = f'Принято {fill.amount}р. от @{fill.user.username}'
    if fill.description:
        reply_text += f': {fill.description}'
    reply_text += f', категория: {fill.category.get_emoji()} {fill.category.name}.'
    if budget:
        reply_text += (
            f'\nИспользовано {current_category_usage.amount:.0f} из {current_category_usage.monthly_limit:.0f}.'
        )
    return reply_text
