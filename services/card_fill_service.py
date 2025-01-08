from collections import defaultdict
import logging
from contextlib import contextmanager
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, extract
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from settings import settings
from model import StoredCardFill, StoredCategory, StoredTelegramUser, StoredFillScope, StoredBudget, StoredCurrencyRate
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

    def list_categories_with_budget(self, scope: FillScope) -> list[tuple[Category, Budget]]:
        budget_cache: dict[Category, Budget] = dict()
        categories = self.list_categories()
        return [(category, self.get_budget_for_category(category, scope, budget_cache)) for category in categories]

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
                .filter(
                    extract("month", StoredCardFill.fill_date).in_([m.value for m in months])
                )
                .all()
            )

            data: dict[Month, dict[Category, float]] = defaultdict(
                lambda: defaultdict(float)
            )
            for fill in fills:
                fill_month = Month(fill.fill_date.month)
                fill_category = fill.category.to_entity_category()
                data[fill_month][fill_category] += fill.amount

            ret: dict[Month, list[CategorySumOverPeriod]] = defaultdict(list)
            budget_cache: dict[Category, Budget] = dict()
            for month, mdata in data.items():
                for category, amount in mdata.items():
                    monthly_limit = None
                    if budget := self.get_budget_for_category(
                        category, scope, cache=budget_cache
                    ):
                        monthly_limit = budget.monthly_limit
                    ret[month].append(
                        CategorySumOverPeriod(
                            amount=amount,
                            category=category,
                            monthly_limit=monthly_limit,
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

    def get_yearly_report(self, year: int, scope: FillScope) -> SummaryOverPeriod:
        with self.db_session() as db_session:
            by_user_query = (
                "select u.user_id, sum(cf.amount) as amount "
                "from card_fill cf "
                "join telegram_user u on cf.user_id = u.user_id "
                f"where year(cf.fill_date) = {year} and cf.fill_scope = {scope.scope_id} "
                "group by u.username"
            )
            by_user_rows = db_session.execute(by_user_query).fetchall()
            by_user: list[UserSumOverPeriod] = []
            for user_id, amount in by_user_rows:
                user = db_session.query(StoredTelegramUser).get(user_id)
                by_user.append(UserSumOverPeriod(user.to_entity_user(), amount))

            by_category_query = (
                "select cat.code as category_code, sum(cf.amount) as amount "
                "from card_fill cf "
                "join category cat on cf.category_code = cat.code "
                f"where year(cf.fill_date) = {year} and cf.fill_scope = {scope.scope_id} "
                "group by cat.code"
            )
            by_category_rows = db_session.execute(by_category_query).fetchall()
            by_category: list[CategorySumOverPeriod] = []
            for category_code, amount in by_category_rows:
                category = db_session.query(StoredCategory).get(category_code)
                by_category.append(
                    CategorySumOverPeriod(
                        category.to_entity_category(), amount, None
                    )
                )

            return SummaryOverPeriod(by_user=by_user, by_category=by_category)

    def get_budget_for_category(
        self,
        category: Category,
        scope: FillScope,
        cache: Optional[dict[Category, Budget]] = None,
    ) -> Optional[Budget]:
        if cache and category in cache:
            return cache[category]

        with self.db_session() as db_session:
            budget = (
                db_session.query(StoredBudget)
                .filter(StoredBudget.category_code == category.code)
                .filter(StoredBudget.fill_scope == scope.scope_id)
                .one_or_none()
            )
            if cache is not None:
                cache[category] = budget
            if budget:
                return budget.to_entity_budget()
            return None

    def get_current_month_budget_usage_for_category(
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
            fills: list[StoredCardFill] = (
                db_session.query(StoredCardFill)
                .filter(StoredCardFill.fill_scope == scope.scope_id)
                .filter(StoredCardFill.is_netted.is_(False))
                .all()
            )
            for fill in fills:
                fill.is_netted = True
                db_session.add(fill)
            db_session.commit()
