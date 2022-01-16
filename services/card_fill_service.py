from typing import Optional, List, Dict, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from settings import database_uri, minor_proportion_user_id, major_proportion_user_id
from model import CardFill, Category, TelegramUser, FillScope, Budget
from dto import (
    Month, FillDto, CategoryDto, UserDto, UserSumOverPeriodDto,
    CategorySumOverPeriodDto, ProportionOverPeriodDto, SummaryOverPeriodDto,
    FillScopeDto, BudgetDto
)
if TYPE_CHECKING:
    from logging import Logger


@dataclass(frozen=True)
class CardFillServiceSettings:
    logger: 'Logger'


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
    def __init__(self, settings: CardFillServiceSettings):
        self.logger = settings.logger
        self._db_engine = create_engine(database_uri, pool_recycle=3600)
        self.logger.info('Initialized db_engine for card fill service')
        self.DbSession = scoped_session(sessionmaker(bind=self._db_engine))

        db_session = self.DbSession()
        try:
            self.minor_proportion_user = db_session.query(TelegramUser).get(minor_proportion_user_id)
            self.major_proportion_user = db_session.query(TelegramUser).get(major_proportion_user_id)
        finally:
            self.DbSession.remove()

    def get_scope(self, chat_id: int) -> FillScopeDto:
        db_session = self.DbSession()
        try:
            scope = db_session.query(FillScope).filter(FillScope.chat_id == chat_id).one_or_none()
            self.logger.info(f'For chat {chat_id} identified scope {scope}')
            return FillScopeDto.from_model(scope)
        finally:
            self.DbSession.remove()

    def handle_new_fill(self, fill: FillDto) -> FillDto:
        db_session = self.DbSession()
        try:
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
                self.logger.info(f'Create new user {user}')

            fill_category = db_session.query(Category).get('OTHER')
            try:
                fill_category: Category = next(
                    filter(lambda cat: cat.fill_fits_category(fill.description), db_session.query(Category).all())
                )
            except StopIteration:
                pass
            fill.category = CategoryDto.from_model(fill_category)

            card_fill = CardFill(
                user_id=user.user_id,
                fill_date=fill.fill_date,
                amount=fill.amount,
                description=fill.description,
                category_code=fill_category.code,
                fill_scope=fill.scope.scope_id,
            )
            db_session.add(card_fill)
            db_session.commit()
            fill.id = card_fill.fill_id
            self.logger.info(f'Save fill {fill}')
            return fill
        finally:
            self.DbSession.remove()

    def get_fill_by_id(self, fill_id: int) -> FillDto:
        db_session = self.DbSession()
        try:
            return FillDto.from_model(db_session.query(CardFill).get(fill_id))
        finally:
            self.DbSession.remove()

    def delete_fill(self, fill: FillDto) -> None:
        db_session = self.DbSession()
        try:
            fill_obj = db_session.query(CardFill).get(fill.id)
            db_session.delete(fill_obj)
            db_session.commit()
            self.logger.info(f'Delete fill {fill}')
        finally:
            self.DbSession.remove()

    def list_categories(self) -> List[CategoryDto]:
        db_session = self.DbSession()
        try:
            return [CategoryDto.from_model(cat) for cat in db_session.query(Category).all()]
        finally:
            self.DbSession.remove()

    def create_new_category(self, category: CategoryDto) -> CategoryDto:
        db_session = self.DbSession()
        try:
            category_obj = Category(
                code=category.code,
                name=category.name,
                aliases='',
                proportion=Decimal(f'{category.proportion:.2f}')
            )
            db_session.add(category_obj)
            db_session.commit()
            self.logger.info(f'Create category {category_obj}')
        finally:
            self.DbSession.remove()

    def change_category_for_fill(self, fill_id: int, target_category_code: str) -> FillDto:
        db_session = self.DbSession()
        try:
            fill = db_session.query(CardFill).get(fill_id)
            category = db_session.query(Category).get(target_category_code)
            old_category = fill.category
            fill.category_code = category.code
            if old_category.code == 'OTHER' and fill.description:
                category.add_alias(fill.description.lower())
                self.logger.info(f'Add alias {fill.description} to category {category}')
            db_session.commit()
            self.logger.info(f'Change category for fill {fill} to {category}')
            return FillDto.from_model(fill)
        finally:
            self.DbSession.remove()

    def get_monthly_report_by_category(
        self, months: List[Month], year: int, scope: FillScopeDto
    ) -> Dict[Month, List[CategorySumOverPeriodDto]]:
        db_session = self.DbSession()
        try:
            data: Dict[Month, List[CategorySumOverPeriodDto]] = {}
            query = (
                'select month_num, category_name, amount, proportion, monthly_limit '
                'from monthly_report_by_category '
                f'where month_num in ({",".join([str(m.value) for m in months])}) '
                f'and fill_year = {year} '
                f'and fill_scope = {scope.scope_id}'
            )
            rows = db_session.execute(query).fetchall()
            for month in months:
                rows_for_month = list(filter(lambda row: row[0] == month.value, rows))
                data_for_month: List[CategorySumOverPeriodDto] = []
                if rows_for_month:
                    for _, category_name, amount, proportion, monthly_limit in rows_for_month:
                        data_for_month.append(
                            CategorySumOverPeriodDto(category_name, amount, float(proportion), monthly_limit)
                        )
                data[month] = data_for_month
            return data
        finally:
            self.DbSession.remove()

    def get_monthly_report_by_user(
        self, months: List[Month], year: int, scope: FillScopeDto
    ) -> Dict[Month, List[UserSumOverPeriodDto]]:
        db_session = self.DbSession()
        try:
            data: Dict[Month, List[UserSumOverPeriodDto]] = {}
            query = (
                'select month_num, username, amount '
                'from monthly_report_by_user '
                f'where month_num in ({",".join([str(m.value) for m in months])}) '
                f'and fill_year = {year} '
                f'and fill_scope = {scope.scope_id}'
            )
            rows = db_session.execute(query).fetchall()
            for month in months:
                rows_for_month = list(filter(lambda row: row[0] == month.value, rows))
                data_for_month: List[UserSumOverPeriodDto] = []
                if rows_for_month:
                    for _, username, amount in rows_for_month:
                        data_for_month.append(UserSumOverPeriodDto(username, amount))
                data[month] = data_for_month
            return data
        finally:
            self.DbSession.remove()

    @staticmethod
    def _get_user_data(data: List[UserSumOverPeriodDto], username: str) -> Optional[UserSumOverPeriodDto]:
        return next(filter(lambda user_data: user_data.username == username, data), None)

    def get_monthly_report(
        self, months: List[Month], year: int, scope: FillScopeDto
    ) -> Dict[Month, SummaryOverPeriodDto]:
        res: Dict[Month, SummaryOverPeriodDto] = {}
        by_user = self.get_monthly_report_by_user(months, year, scope)
        by_category = self.get_monthly_report_by_category(months, year, scope)
        for month in months:
            by_user_month = by_user[month]
            by_category_month = by_category[month]
            minor_user_data = self._get_user_data(by_user_month, self.minor_proportion_user.username)
            major_user_data = self._get_user_data(by_user_month, self.major_proportion_user.username)
            proportion_actual_month = self._calc_proportion_actual(minor_user_data, major_user_data)
            proportion_target_month = self._calc_proportion_target(by_category_month)
            proportions = ProportionOverPeriodDto(
                proportion_target=proportion_target_month, proportion_actual=proportion_actual_month
            )
            res[month] = SummaryOverPeriodDto(
                by_user=by_user_month, by_category=by_category_month, proportions=proportions
            )
        return res

    @staticmethod
    def _calc_proportion_actual(
        minor_user_data: Optional[UserSumOverPeriodDto], major_user_data: Optional[UserSumOverPeriodDto]
    ) -> float:
        """Actual proportion is a current proportion between minor and major users.
        Thus, proportion_actual = sum for minor_user / sum for major_user"""
        if not minor_user_data:
            return 0.0
        if not major_user_data or major_user_data.amount == 0.0:
            return float('nan')
        return minor_user_data.amount / major_user_data.amount

    @staticmethod
    def _calc_proportion_target(data_by_category: List[CategorySumOverPeriodDto]) -> float:
        """Target proportion is calculated from target fraction.
        Target fraction is the target part of total expense considering target fraction for each category.
        Thus, fraction_target = sum(category_i * fraction_i) / sum(category_i)"""
        weighted_amount = 0.0
        total_amount = 0.0
        for category_data in data_by_category:
            weighted_amount += category_data.amount * proportion_to_fraction(category_data.proportion)
            total_amount += category_data.amount
        if total_amount == 0.0:
            return float('nan')
        return fraction_to_proportion(weighted_amount / total_amount)

    def get_user_fills_in_months(
        self, user: UserDto, months: List[Month], year: int, scope: FillScopeDto
    ) -> List[FillDto]:
        db_session = self.DbSession()
        try:
            user_fills = [FillDto.from_model(fill) for fill in db_session.query(TelegramUser).get(user.id).card_fills]
            month_numbers = [month.value for month in months]
            return list(
                filter(
                    lambda cf: (
                        cf.fill_date.month in month_numbers
                        and cf.fill_date.year == year
                        and cf.scope.scope_id == scope.scope_id
                    ),
                    user_fills
                )
            )
        finally:
            self.DbSession.remove()

    def get_yearly_report(self, year: int, scope: FillScopeDto) -> SummaryOverPeriodDto:
        db_session = self.DbSession()
        try:
            by_user_query = (
                'select u.username, sum(cf.amount) as amount '
                'from card_fill cf '
                'join telegram_user u on cf.user_id = u.user_id '
                f'where year(cf.fill_date) = {year} and cf.fill_scope = {scope.scope_id} '
                'group by u.username'
            )
            by_user_rows = db_session.execute(by_user_query).fetchall()
            by_user: List[UserSumOverPeriodDto] = []
            for row in by_user_rows:
                by_user.append(UserSumOverPeriodDto(*row))

            by_category_query = (
                'select cat.name as category_name, sum(cf.amount) as amount, cat.proportion '
                'from card_fill cf '
                'join category cat on cf.category_code = cat.code '
                f'where year(cf.fill_date) = {year} and cf.fill_scope = {scope.scope_id} '
                'group by cat.name, cat.proportion'
            )
            by_category_rows = db_session.execute(by_category_query).fetchall()
            by_category: List[CategorySumOverPeriodDto] = []
            for row in by_category_rows:
                category_name, amount, proportion = row
                by_category.append(CategorySumOverPeriodDto(category_name, amount, float(proportion), None))

            minor_user_data = self._get_user_data(by_user, self.minor_proportion_user.username)
            major_user_data = self._get_user_data(by_user, self.major_proportion_user.username)

            proportion_actual = self._calc_proportion_actual(minor_user_data, major_user_data)
            proportion_target = self._calc_proportion_target(by_category)
            proportions = ProportionOverPeriodDto(
                proportion_actual=proportion_actual, proportion_target=proportion_target
            )

            return SummaryOverPeriodDto(
                by_user=by_user, by_category=by_category, proportions=proportions
            )
        finally:
            self.DbSession.remove()

    def get_budget_for_category(self, category: CategoryDto, scope: FillScopeDto) -> Optional[BudgetDto]:
        db_session = self.DbSession()
        try:
            budget = (
                db_session.query(Budget)
                .filter(
                    Budget.category_code == category.code
                )
                .filter(
                    Budget.fill_scope == scope.scope_id
                )
                .one_or_none()
            )
            if budget:
                return BudgetDto.from_model(budget)
            return None
        finally:
            self.DbSession.remove()

    def get_current_month_budget_usage_for_category(
        self, category: CategoryDto, scope: FillScopeDto
    ) -> Optional[CategorySumOverPeriodDto]:
        current_month, current_year = Month(datetime.now().month), datetime.now().year
        current_month_usage_by_category = self.get_monthly_report_by_category(
            months=[current_month], year=current_year, scope=scope
        )[current_month]
        return next(
            filter(
                lambda cat_data: cat_data.category_name == category.name,
                current_month_usage_by_category
            ), None
        )
