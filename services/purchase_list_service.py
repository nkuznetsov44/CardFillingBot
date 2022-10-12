import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from settings import database_uri
from dto import FillScopeDto, PurchaseListItemDto
from model import PurchaseListItem


class PurchaseListService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db_engine = create_engine(database_uri, pool_recycle=3600)
        self.logger.info(f'Initialized db_engine for purchase list service at {database_uri}')
        self.DbSession = scoped_session(sessionmaker(bind=self._db_engine))

    def add_purchase(self, purchase: PurchaseListItemDto) -> None:
        db_session = self.DbSession()

        try:
            new_item = PurchaseListItem(
                id=None,
                fill_scope=purchase.scope.scope_id,
                name=purchase.name,
                is_active=purchase.is_active
            )

            db_session.add(new_item)
            db_session.commit()

        finally:
            self.DbSession.remove()

    def get_list(self, scope: FillScopeDto) -> list[PurchaseListItemDto]:
        db_session = self.DbSession()

        try:
            items: list[PurchaseListItem] = (
                db_session.query(PurchaseListItem)
                .filter(PurchaseListItem.is_active.is_(True))
                .filter(PurchaseListItem.fill_scope == scope.scope_id)
                .all()
            )

            ret: list[PurchaseListItemDto] = []

            for item in items:
                ret.append(PurchaseListItemDto.from_model(item))

            # ret = [PurchaseListItemDto.from_model(item) for item in items]

            return ret

        finally:
            self.DbSession.remove()
