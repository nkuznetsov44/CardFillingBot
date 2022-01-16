from typing import Optional, List
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from enum import Enum
from telegramapi.types import User as TelegramapiUser
from model import CardFill, FillScope, TelegramUser, Category, Budget


class Month(Enum):
    january = 1
    february = 2
    march = 3
    april = 4
    may = 5
    june = 6
    july = 7
    august = 8
    september = 9
    october = 10
    november = 11
    december = 12


@dataclass_json
@dataclass
class FillScopeDto:
    scope_id: Optional[int]
    scope_type: str
    chat_id: int

    @staticmethod
    def from_model(scope: FillScope) -> 'FillScopeDto':
        return FillScopeDto(
            scope_id=scope.scope_id,
            scope_type=scope.scope_type,
            chat_id=scope.chat_id
        )


@dataclass_json
@dataclass
class CategoryDto:
    code: str
    name: str
    aliases: List[str]
    proportion: float

    @staticmethod
    def from_model(category: Category) -> 'CategoryDto':
        return CategoryDto(
            code=category.code,
            name=category.name,
            aliases=category.get_aliases(),
            proportion=category.proportion
        )


@dataclass_json
@dataclass
class UserDto:
    id: int
    is_bot: bool
    first_name: str
    last_name: str
    username: str
    language_code: str

    @staticmethod
    def from_telegramapi(telegramapi_user: TelegramapiUser) -> 'UserDto':
        return UserDto(
            id=telegramapi_user.user_id,
            is_bot=telegramapi_user.is_bot,
            first_name=telegramapi_user.first_name,
            last_name=telegramapi_user.last_name,
            username=telegramapi_user.username,
            language_code=telegramapi_user.language_code
        )

    @staticmethod
    def from_model(user: TelegramUser) -> 'UserDto':
        return UserDto(
            id=user.user_id,
            is_bot=user.is_bot,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            language_code=user.language_code
        )


@dataclass_json
@dataclass
class FillDto:
    id: Optional[int]
    user: UserDto
    fill_date: datetime
    amount: str
    description: Optional[str]
    category: Optional[CategoryDto]
    scope: FillScopeDto

    @staticmethod
    def from_model(fill: CardFill) -> 'FillDto':
        return FillDto(
            id=fill.fill_id,
            user=UserDto.from_model(fill.user),
            fill_date=fill.fill_date,
            amount=fill.amount,
            description=fill.description,
            category=CategoryDto.from_model(fill.category),
            scope=FillScopeDto.from_model(fill.scope)
        )


@dataclass_json
@dataclass
class BudgetDto:
    id: int
    scope: FillScopeDto
    category: CategoryDto
    monthly_limit: float

    @staticmethod
    def from_model(budget: Budget) -> 'BudgetDto':
        return Budget(
            id=budget.id,
            scope=FillScopeDto.from_model(budget.scope),
            category=CategoryDto.from_model(budget.category),
            monthly_limit=budget.monthly_limit
        )


@dataclass
class UserSumOverPeriodDto:
    username: str
    amount: float


@dataclass
class CategorySumOverPeriodDto:
    category_name: str
    amount: float
    proportion: float
    monthly_limit: Optional[float]


@dataclass
class ProportionOverPeriodDto:
    proportion_target: Optional[float]
    proportion_actual: Optional[float]


@dataclass
class SummaryOverPeriodDto:
    by_user: List[UserSumOverPeriodDto]
    by_category: List[CategorySumOverPeriodDto]
    proportions: ProportionOverPeriodDto
