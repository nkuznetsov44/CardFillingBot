import csv
import io
from aiogram.types import BufferedInputFile
from handlers.base import BaseMessageHandler
from parsers.command import ServiceCommandType, ServiceCommandMessage
from entities import Fill
from settings import settings


class ServiceCommandMessageHandler(BaseMessageHandler[ServiceCommandMessage]):
    async def handle(self, message: ServiceCommandMessage) -> None:
        if message.data == ServiceCommandType.DUMP:
            if message.original_message.from_user.id == settings.admin_user_id:
                fills = self.card_fill_service.get_all_fills()
                await self.bot.send_document(
                    chat_id=message.original_message.chat.id,
                    document=BufferedInputFile(self._to_csv(fills), filename='dump.csv'),
                )
            else:
                await self.bot.send_message(
                    chat_id=message.original_message.chat.id,
                    text='No..',
                )

    def _to_csv(self, fills: list[Fill]) -> bytes:
        with io.StringIO() as iobuf:
            writer = csv.writer(iobuf)
            writer.writerow(('fill_id', 'scope_id', 'user_id', 'fill_date', 'amount', 'category_code', 'description', 'is_netted'))
            for fill in fills:
                writer.writerow(
                    (
                        fill.id,
                        fill.scope.scope_id,
                        fill.user.id,
                        fill.fill_date.isoformat(),
                        fill.amount,
                        fill.category.code,
                        fill.description,
                        fill.is_netted,
                    )
                )
            return iobuf.getvalue().encode()
