from collections import defaultdict
import logging
from contextlib import contextmanager
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, extract
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from settings import settings
from model import StoredCardFill, StoredCategory, StoredTelegramUser, StoredFillScope, StoredBudget, StoredCurrencyRate, StoredIncome
from entities import (
    Month,
    Fill,
    Category,
    User,
    UserSumOverPeriod,
    CategorySumOverPeriod,
    SummaryOverPeriod,
    FillScope,
    Budget,
    UserSumOverPeriodWithBalance,
    Quarter,
    Income,
)


class CardFillService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db_engine = create_engine(settings.database_uri, pool_recycle=3600)
        self.logger.info(
            f"Initialized db_engine for card fill service at {settings.database_uri}"
        )
        self.DbSession = scoped_session(sessionmaker(bind=self._db_engine))

    @contextmanager
    def db_session(self) -> Session:
        db_session = self.DbSession()
        try:
            yield db_session
        finally:
            self.DbSession.remove()

    def get_all_fills(self) -> list[Fill]:
        with self.db_session() as db_session:
            return [f.to_entity_fill() for f in db_session.query(StoredCardFill).all()]

    def get_scope(self, chat_id: int) -> FillScope:
        with self.db_session() as db_session:
            scope: StoredFillScope = (
                db_session.query(StoredFillScope)
                .filter(StoredFillScope.chat_id == chat_id)
                .one_or_none()
            )
            self.logger.info(f"For chat {chat_id} identified scope {scope}")
            return scope.to_entity_fill_scope()

    def handle_new_fill(self, fill: Fill) -> Fill:
        with self.db_session() as db_session:
            user = db_session.query(StoredTelegramUser).get(fill.user.id)
            if not user:
                new_user = StoredTelegramUser(
                    user_id=fill.user.id,
                    is_bot=fill.user.is_bot,
                    first_name=fill.user.first_name,
                    last_name=fill.user.last_name,
                    username=fill.user.username,
                    language_code=fill.user.language_code,
                )
                db_session.add(new_user)
                user = new_user
                self.logger.info(f"Create new user {user}")

            category = StoredCategory.by_desc(
                description=fill.description,
                categories=db_session.query(StoredCategory).all(),
                default=db_session.query(StoredCategory).get("OTHER"),
            )
            fill.category = category.to_entity_category()

            if fill.currency:
                currency = db_session.query(StoredCurrencyRate).get(fill.currency.value)
                fill.amount = fill.amount * currency.rate

            card_fill = StoredCardFill(
                user_id=user.user_id,
                fill_date=fill.fill_date,
                amount=fill.amount,
                description=fill.description,
                category_code=category.code,
                fill_scope=fill.scope.scope_id,
                currency=fill.currency.value if fill.currency else None,
            )

            db_session.add(card_fill)
            db_session.commit()
            fill.id = card_fill.fill_id
            self.logger.info(f"Save fill {fill}")
            return fill

    def get_fill_by_id(self, fill_id: int) -> Fill:
        with self.db_session() as db_session:
            return db_session.query(StoredCardFill).get(fill_id).to_entity_fill()

    def delete_fill(self, fill: Fill) -> None:
        with self.db_session() as db_session:
            fill_obj = db_session.query(StoredCardFill).get(fill.id)
            db_session.delete(fill_obj)
            db_session.commit()
            self.logger.info(f"Delete fill {fill}")

    def change_date_for_fill(self, fill: Fill, dt: datetime) -> None:
        with self.db_session() as db_session:
            fill_obj = db_session.query(StoredCardFill).get(fill.id)
            fill_obj.fill_date = dt
            db_session.add(fill_obj)
            db_session.commit()
            self.logger.info(f"Changed date for fill {fill_obj}")

    def list_categories(self) -> list[Category]:
        with self.db_session() as db_session:
            return [cat.to_entity_category() for cat in db_session.query(StoredCategory).all()]

    def create_new_category(self, category: Category) -> Category:
        with self.db_session() as db_session:
            stored_category = StoredCategory(
                code=category.code,
                name=category.name,
                aliases="",
                emoji_name=category.emoji_name,
            )
            db_session.add(stored_category)
            db_session.commit()
            self.logger.info(f"Create category {stored_category}")
            return stored_category.to_entity_category()

    def change_category_for_fill(
        self, fill_id: int, target_category_code: str
    ) -> Fill:
        with self.db_session() as db_session:
            fill: StoredCardFill = db_session.query(StoredCardFill).get(fill_id)
            category: StoredCategory = db_session.query(StoredCategory).get(target_category_code)
            old_category = fill.category
            fill.category_code = category.code
            if (
                old_category.code == "OTHER"
                and category.code != "OTHER"
                and fill.description
            ):
                category.add_alias(fill.description.lower())
                self.logger.info(f"Add alias {fill.description} to category {category}")
            db_session.commit()
            self.logger.info(f"Change category for fill {fill} to {category}")
            return fill.to_entity_fill()

    def get_monthly_report_by_category(
        self, months: list[Month], year: int, scope: FillScope
    ) -> dict[Month, list[CategorySumOverPeriod]]:
        with self.db_session() as db_session:
            fills: list[StoredCardFill] = (
                db_session.query(StoredCardFill)
                .filter(StoredCardFill.fill_scope.in_(self._get_scope_id_filter(scope)))
                .filter(extract("year", StoredCardFill.fill_date) == year)
                .all()
            )

            monthly_data: dict[Month, dict[Category, float]] = defaultdict(
                lambda: defaultdict(float)
            )
            quarter_data: dict[Quarter, dict[Category, float]] = defaultdict(lambda: defaultdict(float))
            year_data: dict[Category, float] = defaultdict(float)
            for fill in fills:
                fill_month = Month(fill.fill_date.month)
                fill_quarter = Quarter.from_month(fill_month)
                fill_category = fill.category.to_entity_category()
                monthly_data[fill_month][fill_category] += fill.amount
                quarter_data[fill_quarter][fill_category] += fill.amount
                year_data[fill_category] += fill.amount

            ret: dict[Month, list[CategorySumOverPeriod]] = defaultdict(list)
            budgets = {budget.category.code: budget for budget in self.list_budgets(scope)}
            categories = year_data.keys()
            for month in months:
                quarter = Quarter.from_month(month)
                mdata = monthly_data[month]
                qdata = quarter_data[quarter]
                for category in categories:
                    budget = budgets.get(category.code)
                    ret[month].append(
                        CategorySumOverPeriod(
                            category=category,
                            month=month,
                            quarter=quarter,
                            year=year,
                            amount=mdata.get(category, 0),
                            monthly_limit=budget.monthly_limit if budget else None,
                            quarter_amount=qdata.get(category, 0),
                            quarter_limit=budget.quarter_limit if budget else None,
                            year_amount=year_data.get(category, 0),
                            year_limit=budget.year_limit if budget else None,
                        )
                    )
            return ret

    def _get_scope_id_filter(self, scope: FillScope) -> list[int]:
        if scope.report_scopes:
            return scope.report_scopes
        return [scope.scope_id]

    def get_monthly_report_by_user(
        self, months: list[Month], year: int, scope: FillScope
    ) -> dict[Month, list[UserSumOverPeriod]]:
        with self.db_session() as db_session:
            fills: list[StoredCardFill] = (
                db_session.query(StoredCardFill)
                .filter(StoredCardFill.fill_scope.in_(self._get_scope_id_filter(scope)))
                .filter(extract("year", StoredCardFill.fill_date) == year)
                .filter(
                    extract("month", StoredCardFill.fill_date).in_([m.value for m in months])
                )
                .all()
            )

            data: dict[Month, dict[User, float]] = defaultdict(
                lambda: defaultdict(float)
            )
            for fill in fills:
                fill_month = Month(fill.fill_date.month)
                fill_user = fill.user.to_entity_user()
                data[fill_month][fill_user] += fill.amount

            ret: dict[Month, list[UserSumOverPeriod]] = defaultdict(list)
            for month, mdata in data.items():
                for user, amount in mdata.items():
                    ret[month].append(UserSumOverPeriod(user=user, amount=amount))
            return ret

    def get_debt_monthly_report_by_user(
        self, months: list[Month], year: int, scope: FillScope
    ) -> dict[Month, list[UserSumOverPeriodWithBalance]]:
        with self.db_session() as db_session:
            fills: list[StoredCardFill] = (
                db_session.query(StoredCardFill)
                .filter(StoredCardFill.fill_scope == scope.scope_id)
                .filter(extract("year", StoredCardFill.fill_date) == year)
                .filter(
                    extract("month", StoredCardFill.fill_date).in_([m.value for m in months])
                )
                .filter(StoredCardFill.is_netted.is_(False))
                .all()
            )

            data: dict[Month, dict[User, float]] = defaultdict(
                lambda: defaultdict(float)
            )
            for fill in fills:
                fill_month = Month(fill.fill_date.month)
                fill_user = fill.user.to_entity_user()
                data[fill_month][fill_user] += fill.amount

            ret: dict[Month, list[UserSumOverPeriodWithBalance]] = defaultdict(list)
            for month, mdata in data.items():
                month_total = sum(mdata.values())
                num_users = len(mdata)
                for user, amount in mdata.items():
                    ret[month].append(
                        UserSumOverPeriodWithBalance(
                            user=user,
                            amount=amount,
                            balance=(amount - month_total / num_users),
                        )
                    )
            return ret

    def get_monthly_report(
        self, months: list[Month], year: int, scope: FillScope
    ) -> dict[Month, SummaryOverPeriod]:
        res: dict[Month, SummaryOverPeriod] = {}
        by_user = self.get_monthly_report_by_user(months, year, scope)
        by_category = self.get_monthly_report_by_category(months, year, scope)
        for month in months:
            by_user_month = by_user[month]
            by_category_month = by_category[month]
            res[month] = SummaryOverPeriod(
                by_user=by_user_month,
                by_category=by_category_month,
            )
        return res

    def get_user_fills_in_months(
        self, user: User, months: list[Month], year: int, scope: FillScope
    ) -> list[Fill]:
        with self.db_session() as db_session:
            fills: list[StoredCardFill] = (
                db_session.query(StoredCardFill)
                .filter(StoredCardFill.fill_scope == scope.scope_id)
                .filter(StoredCardFill.user_id == user.id)
                .filter(extract("year", StoredCardFill.fill_date) == year)
                .filter(
                    extract("month", StoredCardFill.fill_date).in_([m.value for m in months])
                )
            )
            return [f.to_entity_fill() for f in fills]

    def get_budget_for_category(self, category: Category, scope: FillScope) -> Optional[Budget]:
        with self.db_session() as db_session:
            budget = (
                db_session.query(StoredBudget)
                .filter(StoredBudget.category_code == category.code)
                .filter(StoredBudget.fill_scope == scope.scope_id)
                .one_or_none()
            )
            if budget:
                return budget.to_entity_budget()
            return None

    def list_budgets(self, scope: FillScope) -> list[Budget]:
        with self.db_session() as db_session:
            budgets: list[StoredBudget] = (
                db_session.query(StoredBudget)
                .filter(StoredBudget.fill_scope == scope.scope_id)
                .all()
            )
            return [sb.to_entity_budget() for sb in budgets]

    def get_current_budget_usage_for_category(
        self, category: Category, scope: FillScope
    ) -> Optional[CategorySumOverPeriod]:
        current_month, current_year = Month(datetime.now().month), datetime.now().year
        current_month_usage_by_category = self.get_monthly_report_by_category(
            months=[current_month], year=current_year, scope=scope
        )[current_month]
        return next(
            filter(
                lambda cat_data: cat_data.category.code == category.code,
                current_month_usage_by_category,
            ),
            None,
        )

    def net_balances(self, scope: FillScope) -> None:
        with self.db_session() as db_session:
            fills = (
                db_session.query(StoredCardFill)
                .filter(StoredCardFill.fill_scope.in_(self._get_scope_id_filter(scope)))
                .filter(StoredCardFill.is_netted == False)
                .all()
            )
            for fill in fills:
                fill.is_netted = True
                db_session.add(fill)
            db_session.commit()
            self.logger.info(f"Net {len(fills)} balances for scope {scope.scope_id}")

    def handle_new_income(self, income: Income) -> Income:
        with self.db_session() as db_session:
            user = db_session.query(StoredTelegramUser).get(income.user.id)
            if not user:
                new_user = StoredTelegramUser(
                    user_id=income.user.id,
                    is_bot=income.user.is_bot,
                    first_name=income.user.first_name,
                    last_name=income.user.last_name,
                    username=income.user.username,
                    language_code=income.user.language_code,
                )
                db_session.add(new_user)
                user = new_user
                self.logger.info(f"Create new user {user}")

            # Store original amount and currency for reference
            original_amount = income.amount
            original_currency = income.currency

            # Convert to base currency if needed
            if income.currency:
                currency_rate = db_session.query(StoredCurrencyRate).get(income.currency.value)
                if currency_rate:
                    income.amount = income.amount * currency_rate.rate

            stored_income = StoredIncome(
                user_id=user.user_id,
                income_date=income.income_date,
                amount=income.amount,
                description=income.description,
                fill_scope=income.scope.scope_id,
                currency=income.currency.value if income.currency else None,
                original_amount=original_amount,
                original_currency=original_currency.value if original_currency else None,
            )

            db_session.add(stored_income)
            db_session.commit()
            income.id = stored_income.income_id
            income.original_amount = original_amount
            income.original_currency = original_currency
            self.logger.info(f"Save income {income}")
            return income

    def delete_income(self, income: Income) -> None:
        with self.db_session() as db_session:
            income_obj = db_session.query(StoredIncome).get(income.id)
            db_session.delete(income_obj)
            db_session.commit()
            self.logger.info(f"Delete income {income}")

    def get_user_income_in_months(
        self, user: User, months: list[Month], year: int, scope: FillScope
    ) -> list[Income]:
        with self.db_session() as db_session:
            incomes = (
                db_session.query(StoredIncome)
                .filter(StoredIncome.user_id == user.id)
                .filter(StoredIncome.fill_scope.in_(self._get_scope_id_filter(scope)))
                .filter(extract("year", StoredIncome.income_date) == year)
                .filter(extract("month", StoredIncome.income_date).in_([m.value for m in months]))
                .all()
            )
            return [income.to_entity_income() for income in incomes]

    def get_income_monthly_report_by_user(
        self, months: list[Month], year: int, scope: FillScope
    ) -> dict[Month, list[UserSumOverPeriod]]:
        with self.db_session() as db_session:
            incomes: list[StoredIncome] = (
                db_session.query(StoredIncome)
                .filter(StoredIncome.fill_scope.in_(self._get_scope_id_filter(scope)))
                .filter(extract("year", StoredIncome.income_date) == year)
                .all()
            )

            monthly_data: dict[Month, dict[User, float]] = defaultdict(lambda: defaultdict(float))
            all_users = set()
            for income in incomes:
                income_month = Month(income.income_date.month)
                user = income.user.to_entity_user()
                monthly_data[income_month][user] += income.amount
                all_users.add(user)

            ret: dict[Month, list[UserSumOverPeriod]] = defaultdict(list)
            for month in months:
                for user in all_users:
                    amount = monthly_data[month].get(user, 0)
                    if amount > 0:  # Only include users with income in this month
                        ret[month].append(UserSumOverPeriod(user=user, amount=amount))
            return ret
