from typing import Union, Optional, List, Any, TYPE_CHECKING
import logging
from apscheduler.triggers.date import DateTrigger
from app import scheduler, dp, cache_service

if TYPE_CHECKING:
    from datetime import datetime
    from apscheduler.job import Job
    from aiogram.types import (
        MessageEntity,
        InlineKeyboardMarkup,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
        ForceReply,
    )


logger = logging.getLogger(__name__)


async def _schedule_message_job(
    chat_id: Union[int, str],
    text: str,
    parse_mode: Optional[str] = None,
    entities: Optional[List["MessageEntity"]] = None,
    disable_web_page_preview: Optional[bool] = None,
    disable_notification: Optional[bool] = None,
    reply_to_message_id: Optional[int] = None,
    allow_sending_without_reply: Optional[bool] = None,
    reply_markup: Union[
        "InlineKeyboardMarkup",
        "ReplyKeyboardMarkup",
        "ReplyKeyboardRemove",
        "ForceReply",
        None,
    ] = None,
    context: Optional[Any] = None,
):
    sent_message = await dp.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        entities=entities,
        disable_web_page_preview=disable_web_page_preview,
        disable_notification=disable_notification,
        reply_to_message_id=reply_to_message_id,
        allow_sending_without_reply=allow_sending_without_reply,
        reply_markup=reply_markup,
    )
    if context:
        cache_service.set_context_for_message(sent_message, context)


def schedule_message(
    chat_id: Union[int, str],
    text: str,
    dt: "datetime",
    parse_mode: Optional[str] = None,
    entities: Optional[List["MessageEntity"]] = None,
    disable_web_page_preview: Optional[bool] = None,
    disable_notification: Optional[bool] = None,
    reply_to_message_id: Optional[int] = None,
    allow_sending_without_reply: Optional[bool] = None,
    reply_markup: Union[
        "InlineKeyboardMarkup",
        "ReplyKeyboardMarkup",
        "ReplyKeyboardRemove",
        "ForceReply",
        None,
    ] = None,
    context: Optional[Any] = None,
) -> "Job":
    job = scheduler.add_job(
        func=_schedule_message_job,
        args=(chat_id, text),
        kwargs={
            "parse_mode": parse_mode,
            "entities": entities,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup,
            "context": context,
        },
        trigger=DateTrigger(dt),
    )
    logger.info(f"Scheduled message {text} at {dt} with context {context}")
    return job
