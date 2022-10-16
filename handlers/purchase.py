import logging
from app import bot, cache_service, purchase_service
from parsers.purchase_list import (
    PurchaseMessage,
    DeletePurchaseMessage,
    PurchaseListMessage,
)
from formatters import format_purchase_list


logger = logging.getLogger(__name__)


async def handle_purchase_message(message: PurchaseMessage) -> None:
    purchase = message.data
    purchase_service.add_purchase(purchase)
    await bot.send_message(
        chat_id=message.original_message.chat.id,
        text=f"✔️ {purchase.name} успешно добавлен в список покупок",
    )


async def handle_delete_purchase_message(message: DeletePurchaseMessage):
    purchase_numbers = message.data
    logger.debug(
        f"message: {message.original_message}, reply_to: {message.original_message.reply_to_message}"
    )
    purchase_ids = cache_service.get_purchases_for_message(
        message.original_message.reply_to_message
    )
    for purchase_number in purchase_numbers:
        purchase_id = purchase_ids.get(purchase_number)
        if purchase_id is None:
            raise ValueError(f"Could not find purchase id for number {purchase_number}")
        purchase_service.delete_purchase(purchase_id)
    await bot.send_message(
        chat_id=message.original_message.chat.id, text="Покупки удалены из списка"
    )


async def handle_get_purchases_message(message: PurchaseListMessage) -> None:
    scope = message.data
    purchases = purchase_service.get_list(scope)
    logger.debug(f"Returned from service: {purchases}")

    sent_message = await bot.send_message(
        chat_id=message.original_message.chat.id, text=format_purchase_list(purchases)
    )
    cache_service.set_purchases_for_message(sent_message, purchases)
