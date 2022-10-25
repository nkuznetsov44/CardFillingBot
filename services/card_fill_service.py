from collections import defaultdict
import logging
from contextlib import contextmanager
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, extract
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from settings import database_uri, minor_proportion_user_id, major_proportion_user_id
from model import CardFill, Category, TelegramUser, FillScope, Budget
from dto import (
    Month,
    FillDto,
    CategoryDto,
    UserDto,
    UserSumOverPeriodDto,
    CategorySumOverPeriodDto,
    ProportionOverPeriodDto,
    SummaryOverPeriodDto,
    FillScopeDto,
    BudgetDto,
    UserSumOverPeriodWithBalanceDto,
)


def proportion_to_fraction(proportion: float) -> float:
    """Considering total consists of two parts.
    Proportion is the proportion of two parts.
    Fraction is the fraction of the minor part in total.

    """
    return proportion / (1 + proportion)


def fraction_to_proportion(fraction: float) -> float:
    """Considering total consists of two parts.
    Proportion is the proportion of two parts.
    Fraction is the fraction of the minor part in total.

    """
    return fraction / (1 - fraction)


class CardFillService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db_engine = create_engine(database_uri, pool_recycle=3600)
        self.logger.info(
            f"Initialized db_engine for card fill service at {database_uri}"
        )
        self.DbSession = scoped_session(sessionmaker(bind=self._db_engine))
        self._init_proportion_users()

    @contextmanager
    def db_session(self) -> Session:
        db_session = self.DbSession()
        try:
            yield db_session
        finally:
            self.DbSession.remove()

    def _init_proportion_users(self) -> None:
        with self.db_session() as db_session:
            self.minor_proportion_user = db_session.query(TelegramUser).get(
                minor_proportion_user_id
            )
            self.major_proportion_user = db_session.query(TelegramUser).get(
                major_proportion_user_id
            )

    def get_scope(self, chat_id: int) -> FillScopeDto:
        with self.db_session() as db_session:
            scope = (
                db_session.query(FillScope)
                .filter(FillScope.chat_id == chat_id)
                .one_or_none()
            )
            self.logger.info(f"For chat {chat_id} identified scope {scope}")
            return FillScopeDto.from_model(scope)

    def handle_new_fill(self, fill: FillDto) -> FillDto:
        with self.db_session() as db_session:
            user = db_session.query(TelegramUser).get(fill.user.id)
            if not user:
                new_user = TelegramUser(
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

            category = Category.by_desc(
                description=fill.description,
                categories=db_session.query(Category).all(),
                default=db_session.query(Category).get("OTHER"),
            )
            fill.category = CategoryDto.from_model(category)

            card_fill = CardFill(
                user_id=user.user_id,
                fill_date=fill.fill_date,
                amount=fill.amount,
                description=fill.description,
                category_code=category.code,
                fill_scope=fill.scope.scope_id,
            )

            db_session.add(card_fill)
            db_session.commit()
            fill.id = card_fill.fill_id
            self.logger.info(f"Save fill {fill}")
            return fill

    def get_fill_by_id(self, fill_id: int) -> FillDto:
        with self.db_session() as db_session:
            return FillDto.from_model(db_session.query(CardFill).get(fill_id))

    def delete_fill(self, fill: FillDto) -> None:
        with self.db_session() as db_session:
            fill_obj = db_session.query(CardFill).get(fill.id)
            db_session.delete(fill_obj)
            db_session.commit()
            self.logger.info(f"Delete fill {fill}")

    def change_date_for_fill(self, fill: FillDto, dt: datetime) -> None:
        with self.db_session() as db_session:
            fill_obj = db_session.query(CardFill).get(fill.id)
            fill_obj.fill_date = dt
            db_session.add(fill_obj)
            db_session.commit()
            self.logger.info(f"Changed date for fill {fill_obj}")

    def list_categories(self) -> list[CategoryDto]:
        with self.db_session() as db_session:
            return list(map(CategoryDto.from_model, db_session.query(Category).all()))

    def create_new_category(self, category: CategoryDto) -> CategoryDto:
        with self.db_session() as db_session:
            category_obj = Category(
                code=category.code,
                name=category.name,
                aliases="",
                proportion=Decimal(f"{category.proportion:.2f}"),
                emoji_name=category.emoji_name,
            )
            db_session.add(category_obj)
            db_session.commit()
            self.logger.info(f"Create category {category_obj}")
            return CategoryDto.from_model(category_obj)

    def change_category_for_fill(
        self, fill_id: int, target_category_code: str
    ) -> FillDto:
        with self.db_session() as db_session:
            fill = db_session.query(CardFill).get(fill_id)
            category = db_session.query(Category).get(target_category_code)
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
            return FillDto.from_model(fill)

    def get_monthly_report_by_category(
        self, months: list[Month], year: int, scope: FillScopeDto
    ) -> dict[Month, list[CategorySumOverPeriodDto]]:
        with self.db_session() as db_session:
            fills: list[CardFill] = (
                db_session.query(CardFill)
                .filter(CardFill.fill_scope == scope.scope_id)
                .filter(extract("year", CardFill.fill_date) == year)
                .filter(
                    extract("month", CardFill.fill_date).in_([m.value for m in months])
                )
                .all()
            )

            data: dict[Month, dict[CategoryDto, float]] = defaultdict(lambda: defaultdict(float))
            for fill in fills:
                fill_month = Month(fill.fill_date.month)
                fill_category = CategoryDto.from_model(fill.category)
                data[fill_month][fill_category] += fill.amount

            ret: dict[Month, list[CategorySumOverPeriodDto]] = defaultdict(list)
            budget_cache: dict[CategoryDto, BudgetDto] = dict()
            for month, mdata in data.items():
                for category, amount in mdata.items():
                    monthly_limit = None
                    if budget := self.get_budget_for_category(
                        category, scope, cache=budget_cache
                    ):
                        monthly_limit = budget.monthly_limit
                    ret[month].append(
                        CategorySumOverPeriodDto(
                            amount=amount,
                            category=category,
                            monthly_limit=monthly_limit,
                        )
                    )
            return ret

    def get_monthly_report_by_user(
        self, months: list[Month], year: int, scope: FillScopeDto
    ) -> dict[Month, list[UserSumOverPeriodDto]]:
        with self.db_session() as db_session:
            fills: list[CardFill] = (
                db_session.query(CardFill)
                .filter(CardFill.fill_scope == scope.scope_id)
                .filter(extract("year", CardFill.fill_date) == year)
                .filter(
                    extract("month", CardFill.fill_date).in_([m.value for m in months])
                )
                .all()
            )

            data: dict[Month, dict[UserDto, float]] = defaultdict(lambda: defaultdict(float))
            for fill in fills:
                fill_month = Month(fill.fill_date.month)
                fill_user = UserDto.from_model(fill.user)
                data[fill_month][fill_user] += fill.amount

            ret: dict[Month, list[UserSumOverPeriodDto]] = defaultdict(list)
            for month, mdata in data.items():
                for user, amount in mdata.items():
                    ret[month].append(UserSumOverPeriodDto(user=user, amount=amount))
            return ret

    def get_debt_monthly_report_by_user(
        self, months: list[Month], year: int, scope: FillScopeDto
    ) -> dict[Month, list[UserSumOverPeriodWithBalanceDto]]:
        with self.db_session() as db_session:
            fills: list[CardFill] = (
                db_session.query(CardFill)
                .filter(CardFill.fill_scope == scope.scope_id)
                .filter(extract("year", CardFill.fill_date) == year)
                .filter(
                    extract("month", CardFill.fill_date).in_([m.value for m in months])
                )
                .filter(CardFill.is_netted.is_(False))
                .all()
            )

            data: dict[Month, dict[UserDto, float]] = defaultdict(lambda: defaultdict(float))
            for fill in fills:
                fill_month = Month(fill.fill_date.month)
                fill_user = UserDto.from_model(fill.user)
                data[fill_month][fill_user] += fill.amount

            ret: dict[Month, list[UserSumOverPeriodWithBalanceDto]] = defaultdict(list)
            for month, mdata in data.items():
                month_total = sum(mdata.values())
                num_users = len(mdata)
                for user, amount in mdata.items():
                    ret[month].append(
                        UserSumOverPeriodWithBalanceDto(
                            user=user,
                            amount=amount,
                            balance=(amount - month_total / num_users),
                        )
                    )
            return ret

    @staticmethod
    def _get_user_data(
        data: list[UserSumOverPeriodDto], username: str
    ) -> Optional[UserSumOverPeriodDto]:
        return next(
            filter(lambda user_data: user_data.user.username == username, data), None
        )

    def get_monthly_report(
        self, months: list[Month], year: int, scope: FillScopeDto
    ) -> dict[Month, SummaryOverPeriodDto]:
        res: dict[Month, SummaryOverPeriodDto] = {}
        by_user = self.get_monthly_report_by_user(months, year, scope)
        by_category = self.get_monthly_report_by_category(months, year, scope)
        for month in months:
            by_user_month = by_user[month]
            by_category_month = by_category[month]
            minor_user_data = self._get_user_data(
                by_user_month, self.minor_proportion_user.username
            )
            major_user_data = self._get_user_data(
                by_user_month, self.major_proportion_user.username
            )
            proportion_actual_month = self._calc_proportion_actual(
                minor_user_data, major_user_data
            )
            proportion_target_month = self._calc_proportion_target(by_category_month)
            proportions = ProportionOverPeriodDto(
                proportion_target=proportion_target_month,
                proportion_actual=proportion_actual_month,
            )
            res[month] = SummaryOverPeriodDto(
                by_user=by_user_month,
                by_category=by_category_month,
                proportions=proportions,
            )
        return res

    @staticmethod
    def _calc_proportion_actual(
        minor_user_data: Optional[UserSumOverPeriodDto],
        major_user_data: Optional[UserSumOverPeriodDto],
    ) -> float:
        """Actual proportion is a current proportion between minor and major users.
        Thus, proportion_actual = sum for minor_user / sum for major_user"""
        if not minor_user_data:
            return 0.0
        if not major_user_data or major_user_data.amount == 0.0:
            return float("nan")
        return minor_user_data.amount / major_user_data.amount

    @staticmethod
    def _calc_proportion_target(
        data_by_category: list[CategorySumOverPeriodDto],
    ) -> float:
        """Target proportion is calculated from target fraction.
        Target fraction is the target part of total expense considering target fraction for each category.
        Thus, fraction_target = sum(category_i * fraction_i) / sum(category_i)"""
        weighted_amount = 0.0
        total_amount = 0.0
        for category_data in data_by_category:
            weighted_amount += category_data.amount * proportion_to_fraction(
                category_data.category.proportion
            )
            total_amount += category_data.amount
        if total_amount == 0.0:
            return float("nan")
        return fraction_to_proportion(weighted_amount / total_amount)

    def get_user_fills_in_months(
        self, user: UserDto, months: list[Month], year: int, scope: FillScopeDto
    ) -> list[FillDto]:
        with self.db_session() as db_session:
            fills: list[CardFill] = (
                db_session.query(CardFill)
                .filter(CardFill.fill_scope == scope.scope_id)
                .filter(CardFill.user_id == user.id)
                .filter(extract("year", CardFill.fill_date) == year)
                .filter(
                    extract("month", CardFill.fill_date).in_([m.value for m in months])
                )
            )
            return list(map(FillDto.from_model, fills))

    def get_yearly_report(self, year: int, scope: FillScopeDto) -> SummaryOverPeriodDto:
        with self.db_session() as db_session:
            by_user_query = (
                "select u.user_id, sum(cf.amount) as amount "
                "from card_fill cf "
                "join telegram_user u on cf.user_id = u.user_id "
                f"where year(cf.fill_date) = {year} and cf.fill_scope = {scope.scope_id} "
                "group by u.username"
            )
            by_user_rows = db_session.execute(by_user_query).fetchall()
            by_user: list[UserSumOverPeriodDto] = []
            for user_id, amount in by_user_rows:
                user = db_session.query(TelegramUser).get(user_id)
                by_user.append(UserSumOverPeriodDto(UserDto.from_model(user), amount))

            by_category_query = (
                "select cat.code as category_code, sum(cf.amount) as amount "
                "from card_fill cf "
                "join category cat on cf.category_code = cat.code "
                f"where year(cf.fill_date) = {year} and cf.fill_scope = {scope.scope_id} "
                "group by cat.name, cat.proportion"
            )
            by_category_rows = db_session.execute(by_category_query).fetchall()
            by_category: list[CategorySumOverPeriodDto] = []
            for category_code, amount in by_category_rows:
                category = db_session.query(Category).get(category_code)
                by_category.append(
                    CategorySumOverPeriodDto(
                        CategoryDto.from_model(category), amount, None
                    )
                )

            minor_user_data = self._get_user_data(
                by_user, self.minor_proportion_user.username
            )
            major_user_data = self._get_user_data(
                by_user, self.major_proportion_user.username
            )

            proportion_actual = self._calc_proportion_actual(
                minor_user_data, major_user_data
            )
            proportion_target = self._calc_proportion_target(by_category)
            proportions = ProportionOverPeriodDto(
                proportion_actual=proportion_actual, proportion_target=proportion_target
            )

            return SummaryOverPeriodDto(
                by_user=by_user, by_category=by_category, proportions=proportions
            )

    def get_budget_for_category(
        self,
        category: CategoryDto,
        scope: FillScopeDto,
        cache: Optional[dict[CategoryDto, BudgetDto]] = None,
    ) -> Optional[BudgetDto]:
        if cache and category in cache:
            return cache[CategoryDto]

        with self.db_session() as db_session:
            budget = (
                db_session.query(Budget)
                .filter(Budget.category_code == category.code)
                .filter(Budget.fill_scope == scope.scope_id)
                .one_or_none()
            )
            if cache is not None:
                cache[category] = budget
            if budget:
                return BudgetDto.from_model(budget)
            return None

    def get_current_month_budget_usage_for_category(
        self, category: CategoryDto, scope: FillScopeDto
    ) -> Optional[CategorySumOverPeriodDto]:
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
