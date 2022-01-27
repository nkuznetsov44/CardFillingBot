from typing import List
import re
from sqlalchemy import Column, ForeignKey, Integer, Boolean, String, DateTime, Float, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class CardFill(Base):
    __tablename__ = 'card_fill'

    fill_id = Column('fill_id', Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('telegram_user.user_id'))
    user = relationship('TelegramUser', back_populates='card_fills')
    fill_date = Column('fill_date', DateTime)
    amount = Column('amount', Float)
    description = Column('description', String, nullable=True)
    category_code = Column(String, ForeignKey('category.code'))
    category = relationship('Category', back_populates='card_fills', lazy='subquery')
    fill_scope = Column(Integer, ForeignKey('fill_scope.scope_id'))
    scope = relationship('FillScope', back_populates='card_fills', lazy='subquery')

    def __repr__(self) -> str:
        return (
            f'{super().__repr__()}: '
            f'<"fill_id": {self.fill_id}, "user": {self.user}, '
            f'"fill_date": {self.fill_date}, "amount": {self.amount}, '
            f'"description": {self.description}, "category": {self.category},'
            f'"scope": {self.scope}>'
        )


class TelegramUser(Base):
    __tablename__ = 'telegram_user'

    user_id = Column('user_id', Integer, primary_key=True)
    is_bot = Column('is_bot', Boolean)
    first_name = Column('first_name', String, nullable=True)
    last_name = Column('last_name', String, nullable=True)
    username = Column('username', String, nullable=True)
    language_code = Column('language_code', String, nullable=True)
    card_fills = relationship('CardFill')

    def __repr__(self) -> str:
        return (
            f'{super().__repr__()}: '
            f'<"user_id": {self.user_id}, "username": {self.username}>'
        )


class Category(Base):
    __tablename__ = 'category'

    code = Column('code', String, primary_key=True)
    name = Column('name', String)
    aliases = Column('aliases', String)
    proportion = Column('proportion', Numeric)
    emoji_name = Column('emoji_name', String)
    card_fills = relationship('CardFill')

    def get_aliases(self) -> List[str]:
        if self.aliases == '':
            return []
        return self.aliases.split(',')

    def add_alias(self, alias: str) -> None:
        aliases = self.get_aliases()
        aliases.append(alias)
        self.aliases = ','.join(aliases)

    def fill_fits_category(self, fill_description: str) -> bool:
        aliases_re = [re.compile(alias, re.IGNORECASE) for alias in self.get_aliases()]
        return any(pattern.match(fill_description) for pattern in aliases_re)

    def __repr__(self) -> str:
        return (
            f'{super().__repr__()}: '
            f'<"code": {self.code}, "name": {self.name}, "proportion": {self.proportion}>'
        )


class FillScope(Base):
    __tablename__ = 'fill_scope'

    scope_id = Column('scope_id', Integer, primary_key=True)
    scope_type = Column('scope_type', String)
    chat_id = Column('chat_id', Integer)
    card_fills = relationship('CardFill')

    def __repr__(self) -> str:
        return (
            f'{super().__repr__()}: '
            f'<"scope_id": {self.scope_id}, "scope_type": {self.scope_type}, "chat_id": {self.chat_id}>'
        )


class Budget(Base):
    __tablename__ = 'budget'

    id = Column('id', Integer, primary_key=True)
    fill_scope = Column(Integer, ForeignKey('fill_scope.scope_id'))
    scope = relationship('FillScope', lazy='subquery')
    category_code = Column(String, ForeignKey('category.code'))
    category = relationship('Category', lazy='subquery')
    monthly_limit = Column('monthly_limit', Float)

    def __repr__(self) -> str:
        return (
            f'{super().__repr__()}: '
            f'<"id": {self.id}, "fill_scope":{self.fill_scope}, '
            f'"category_code": {self.category_code}, "monthly_limit": {self.monthly_limit}>'
        )
