from typing import Iterable, TypeVar
import re
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Boolean,
    String,
    DateTime,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from entities import FillScope, Category, User, Fill, Budget, PurchaseListItem, CurrencyRate, Currency, Income


Base = declarative_base()


class StoredCardFill(Base):
    __tablename__ = "card_fill"

    fill_id = Column("fill_id", Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("telegram_user.user_id"))
    user = relationship("StoredTelegramUser", back_populates="card_fills")
    fill_date = Column("fill_date", DateTime)
    amount = Column("amount", Float)
    description = Column("description", String, nullable=True)
    category_code = Column(String, ForeignKey("category.code"))
    category = relationship("StoredCategory", back_populates="card_fills", lazy="subquery")
    fill_scope = Column(Integer, ForeignKey("fill_scope.scope_id"))
    scope = relationship("StoredFillScope", back_populates="card_fills", lazy="subquery")
    is_netted = Column("is_netted", Boolean, default=False)
    currency = Column("currency", String)

    def to_entity_fill(self) -> Fill:
        return Fill(
            id=self.fill_id,
            user=self.user.to_entity_user(),
            fill_date=self.fill_date,
            amount=self.amount,
            description=self.description,
            category=self.category.to_entity_category(),
            scope=self.scope.to_entity_fill_scope(),
            is_netted=self.is_netted,
            currency=Currency(self.currency) if self.currency else None,
        )

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()}: "
            f'<"fill_id": {self.fill_id}, "user": {self.user}, '
            f'"fill_date": {self.fill_date}, "amount": {self.amount}, '
            f'"description": {self.description}, "category": {self.category},'
            f'"scope": {self.scope},'
            f'"currency: {self.currency}>'
        )


class StoredTelegramUser(Base):
    __tablename__ = "telegram_user"

    user_id = Column("user_id", Integer, primary_key=True)
    is_bot = Column("is_bot", Boolean)
    first_name = Column("first_name", String, nullable=True)
    last_name = Column("last_name", String, nullable=True)
    username = Column("username", String, nullable=True)
    language_code = Column("language_code", String, nullable=True)
    card_fills = relationship("StoredCardFill")
    incomes = relationship("StoredIncome")

    def to_entity_user(self) -> User:
        return User(
            id=self.user_id,
            is_bot=self.is_bot,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            language_code=self.language_code,
        )

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()}: "
            f'<"user_id": {self.user_id}, "username": {self.username}>'
        )


TStoredCategory = TypeVar('TStoredCategory', bound='StoredCategory')


class StoredCategory(Base):
    __tablename__ = "category"

    code = Column("code", String, primary_key=True)
    name = Column("name", String)
    aliases = Column("aliases", String)
    emoji_name = Column("emoji_name", String)
    card_fills = relationship("StoredCardFill")

    def get_aliases(self) -> list[str]:
        if self.aliases == "":
            return []
        return self.aliases.split(",")

    def add_alias(self, alias: str) -> None:
        aliases = self.get_aliases()
        aliases.append(alias)
        self.aliases = ",".join(aliases)

    def desc_fits_category(self, description: str) -> bool:
        aliases_re = [re.compile(alias, re.IGNORECASE) for alias in self.get_aliases()]
        return any(pattern.match(description) for pattern in aliases_re)

    @classmethod
    def by_desc(
        cls: TStoredCategory, description: str, categories: Iterable[TStoredCategory], default: TStoredCategory
    ) -> TStoredCategory:
        return next(
            filter(lambda cat: cat.desc_fits_category(description), categories),
            default,
        )

    def to_entity_category(self) -> Category:
        return Category(
            code=self.code,
            name=self.name,
            aliases=tuple(self.get_aliases()),
            emoji_name=self.emoji_name,
        )

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()}: "
            f'<"code": {self.code}, "name": {self.name}>'
        )


class StoredFillScope(Base):
    __tablename__ = "fill_scope"

    scope_id = Column("scope_id", Integer, primary_key=True)
    scope_type = Column("scope_type", String)
    chat_id = Column("chat_id", Integer)
    report_scopes = Column("report_scopes", JSON)
    card_fills = relationship("StoredCardFill")

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()}: "
            f'<"scope_id": {self.scope_id}, "scope_type": {self.scope_type}, "chat_id": {self.chat_id}>'
        )

    def to_entity_fill_scope(self) -> FillScope:
        return FillScope(
            scope_id=self.scope_id, scope_type=self.scope_type, chat_id=self.chat_id, report_scopes=self.report_scopes
        )


class StoredCurrencyRate(Base):
    __tablename__ = "currency_rate"

    currency = Column("currency", String, primary_key=True)
    rate = Column("rate", Float)

    def to_entity_currency_rate(self) -> CurrencyRate:
        return CurrencyRate(currency=Currency(self.currency), rate=self.rate)


class StoredBudget(Base):
    __tablename__ = "budget"

    id = Column("id", Integer, primary_key=True)
    fill_scope = Column(Integer, ForeignKey("fill_scope.scope_id"))
    scope = relationship("StoredFillScope", lazy="subquery")
    category_code = Column(String, ForeignKey("category.code"))
    category = relationship("StoredCategory", lazy="subquery")
    monthly_limit = Column("monthly_limit", Float)
    quarter_limit = Column("quarter_limit", Float)
    year_limit = Column("year_limit", Float)

    def to_entity_budget(self) -> Budget:
        return Budget(
            id=self.id,
            scope=self.scope.to_entity_fill_scope(),
            category=self.category.to_entity_category(),
            monthly_limit=self.monthly_limit,
            quarter_limit=self.quarter_limit,
            year_limit=self.year_limit,
        )

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()}: "
            f'<"id": {self.id}, "fill_scope":{self.fill_scope}, '
            f'"category_code": {self.category_code}, "monthly_limit": {self.monthly_limit}>'
        )


class StoredPurchaselistItem(Base):
    __tablename__ = "purchase_list"

    id = Column("id", Integer, primary_key=True)
    fill_scope = Column(Integer, ForeignKey("fill_scope.scope_id"))
    scope = relationship("StoredFillScope", lazy="subquery")
    name = Column(String)
    is_active = Column(Boolean, default=True)

    def to_entity_purchase_list_item(self) -> PurchaseListItem:
        return PurchaseListItem(
            id=self.id,
            scope=self.scope.to_entity_fill_scope(),
            name=self.name,
            is_active=self.is_active,
        )

    def __repr__(self) -> str:
        return f"{super().__repr__()}: " f'<"id": {self.id}, "name": {self.name}>'


class StoredIncome(Base):
    __tablename__ = "income"

    income_id = Column("income_id", Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("telegram_user.user_id"))
    user = relationship("StoredTelegramUser", back_populates="incomes")
    income_date = Column("income_date", DateTime)
    amount = Column("amount", Float)
    description = Column("description", String, nullable=True)
    fill_scope = Column(Integer, ForeignKey("fill_scope.scope_id"))
    scope = relationship("StoredFillScope", lazy="subquery")
    currency = Column("currency", String)
    original_amount = Column("original_amount", Float, nullable=True)
    original_currency = Column("original_currency", String, nullable=True)

    def to_entity_income(self) -> Income:
        return Income(
            id=self.income_id,
            user=self.user.to_entity_user(),
            income_date=self.income_date,
            amount=self.amount,
            description=self.description,
            scope=self.scope.to_entity_fill_scope(),
            currency=Currency(self.currency) if self.currency else None,
            original_amount=self.original_amount,
            original_currency=Currency(self.original_currency) if self.original_currency else None,
        )

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()}: "
            f'<"income_id": {self.income_id}, "user": {self.user}, '
            f'"income_date": {self.income_date}, "amount": {self.amount}, '
            f'"description": {self.description}, "scope": {self.scope},'
            f'"currency: {self.currency}>'
        )
