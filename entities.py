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


@dataclass(frozen=True)
class PurchaseListItem:
    id: int
    scope: FillScope
    name: str
    is_active: Optional[bool] = None


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
    amount: float
    monthly_limit: Optional[float]


@dataclass(frozen=True)
class SummaryOverPeriod:
    by_user: tuple[UserSumOverPeriod]
    by_category: tuple[CategorySumOverPeriod]
