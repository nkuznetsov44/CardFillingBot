from typing import Optional, TypeVar
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, unique
from emoji import emojize
from aiogram.types import User as TelegramapiUser


@unique
class AppMode(Enum):
    POLLING = 'POLLING'
    WEBHOOK = 'WEBHOOK'


@unique
class ServiceCommandType(Enum):
    DUMP = 'dump'


@unique
class Currency(Enum):
    RUB = 'RUB'
    EUR = 'EUR'

    @staticmethod
    def get_by_alias(alias: str) -> 'Currency':
        return {
            'r': Currency.RUB,
            'e': Currency.EUR,
            'р': Currency.RUB,
            'е': Currency.EUR,
        }[alias]


@dataclass
class CurrencyRate:
    currency: Currency
    rate: float


@unique
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


@unique
class Quarter(Enum):
    q1 = 1
    q2 = 2
    q3 = 3
    q4 = 4

    @classmethod
    def from_month(cls, month: Month) -> 'Quarter':
        match month.value:
            case 1 | 2 | 3:
                return cls.q1
            case 4 | 5 | 6:
                return cls.q2
            case 7 | 8 | 9:
                return cls.q3
            case 10 | 11 | 12:
                return cls.q4
            case _:
                raise ValueError(f'Unexpected month value {month}')


@dataclass(frozen=True)
class FillScope:
    scope_id: Optional[int]
    scope_type: str
    chat_id: int
    report_scopes: Optional[list[int]] = None


@dataclass(frozen=True)
class Category:
    code: str
    name: str
    aliases: tuple[str]
    emoji_name: str

    def get_emoji(self) -> str:
        return emojize(self.emoji_name)


TUser = TypeVar('TUser', bound='User')


@dataclass(frozen=True)
class User:
    id: int
    is_bot: bool
    first_name: str
    last_name: str
    username: str
    language_code: str

    @classmethod
    def from_telegramapi(cls: TUser, telegramapi_user: TelegramapiUser) -> TUser:
        return cls(
            id=telegramapi_user.id,
            is_bot=telegramapi_user.is_bot,
            first_name=telegramapi_user.first_name,
            last_name=telegramapi_user.last_name,
            username=telegramapi_user.username,
            language_code=telegramapi_user.language_code,
        )


@dataclass
class Fill:
    id: Optional[int]
    user: User
    fill_date: datetime
    amount: float
    description: Optional[str]
    category: Optional[Category]
    scope: FillScope
    is_netted: bool = False
    currency: Optional[Currency] = None


@dataclass(frozen=True)
class Budget:
    id: int
    scope: FillScope
    category: Category
    monthly_limit: float
    quarter_limit: Optional[float] = None
    year_limit: Optional[float] = None


@dataclass(frozen=True)
class UserSumOverPeriod:
    user: User
    amount: float


@dataclass(frozen=True)
class UserSumOverPeriodWithBalance:
    user: User
    amount: float
    balance: float


@dataclass(frozen=True)
class CategorySumOverPeriod:
    category: Category
    month: Month
    quarter: Quarter
    year: int
    amount: float
    monthly_limit: Optional[float]
    quarter_amount: float
    quarter_limit: Optional[float]
    year_amount: float
    year_limit: Optional[float]


@dataclass(frozen=True)
class SummaryOverPeriod:
    by_user: tuple[UserSumOverPeriod]
    by_category: tuple[CategorySumOverPeriod]
