from typing import Optional, List
from enum import Enum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, Undefined, config


class ChatAction(Enum):
    typing = 'typing'
    upload_photo = 'upload_photo'
    record_video = 'record_video'
    upload_video = 'upload_video'
    record_audio = 'record_audio'
    upload_audio = 'upload_audio'
    upload_document = 'upload_document'
    find_location = 'find_location'
    record_video_note = 'record_video_note'
    upload_video_note = 'upload_video_note'


class ParseMode(Enum):
    Markdown = 'Markdown'
    MarkdownV2 = 'MarkdownV2'
    HTML = 'HTML'


class UpdateType(Enum):
    message = 'message'
    edited_message = 'edited_message'
    channel_post = 'channel_post'
    edited_channel_post = 'edited_channel_post'
    inline_query = 'inline_query'
    chosen_inline_result = 'chosen_inline_result'
    callback_query = 'callback_query'
    shipping_query = 'shipping_query'
    pre_checkout_query = 'pre_checkout_query'
    poll = 'poll'
    poll_answer = 'poll_answer'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class User:
    user_id: int = field(metadata=config(field_name='id'))
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    can_join_groups: Optional[bool] = None
    can_read_all_group_messages: Optional[bool] = None
    supports_inline_queries: Optional[bool] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Chat:
    chat_id: int = field(metadata=config(field_name='id'))
    chat_type: str = field(metadata=config(field_name='type'))
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # photo: Optional[ChatPhoto] = None
    description: Optional[str] = None
    invite_link: Optional[str] = None
    pinned_message: Optional['Message'] = None
    # permissions: Optional[ChatPermissions] = None
    show_mode_delay: Optional[int] = None
    sticker_set_name: Optional[str] = None
    can_set_sticker_set: Optional[bool] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class InlineKeyboardButton:
    text: str
    # url: Optional[str] = None
    # login_url: Optional[LoginUrl] = None
    callback_data: Optional[str] = None
    # switch_inline_query: Optional[str] = None
    # switch_inline_query_current_chat: Optional[str] = None
    # callback_game: Optional[CallbackGame] = None
    # pay: Optional[bool] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class InlineKeyboardMarkup:
    inline_keyboard: List[List[InlineKeyboardButton]]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class KeyboardButton:
    text: str
    request_contact: Optional[bool] = None
    request_location: Optional[bool] = None
    # request_poll: Optional[KeyboardButtonPollType]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ReplyKeyboardMarkup:
    keyboard: List[List[KeyboardButton]]
    resize_keyboard: Optional[bool] = None
    one_time_keyboard: Optional[bool] = None
    selective: Optional[bool] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Message:
    message_id: int
    date: int
    """
    metadata=config(
            encoder= date.isoformat,
            decoder= date.fromisoformat,
            mm_field= fields.DateTime(format='iso')
        ))
    """
    chat: Chat
    forward_from: Optional[User] = None
    forward_from_chat: Optional[Chat] = None
    forward_from_message_id: Optional[int] = None
    forward_signature: Optional[str] = None
    forward_sender_name: Optional[str] = None
    forward_date: Optional[int] = None
    reply_to_message: Optional['Message'] = None
    via_bot: Optional[User] = None
    edit_date: Optional[int] = None
    media_group_id: Optional[str] = None
    author_signature: Optional[str] = None
    text: Optional[str] = None
    # entities: Optional[List[MessageEntity]] = None
    # animation: Optional[Animation] = None
    # audio: Optional[Audio] = None
    # document: Optional[Document] = None
    # photo: Optional[List[PhotoSize]] = None
    # sticker: Optional[Sticker] = None
    # video: Optional[Video] = None
    # video_note: Optional[VideoNote] = None
    # voice: Optional[Voice] = None
    caption: Optional[str] = None
    # caption_entity: Optional[List[MessageEntity]] = None
    # contact: Optional[Contact] = None
    # dice: Optional[Dice] = None
    # game: Optional[Game] = None
    # poll: Optional[Poll] = None
    # venue: Optional[Venue] = None
    # location: Optional[Location] = None
    new_chat_members: Optional[List[User]] = None
    left_chat_member: Optional[User] = None
    new_chat_title: Optional[str] = None
    # new_chat_photo: Optional[List[PhotoSize]] = None
    delete_chat_photo: Optional[bool] = None
    group_chat_created: Optional[bool] = None
    supergroup_chat_created: Optional[bool] = None
    channel_chat_created: Optional[bool] = None
    migrate_to_chat_id: Optional[int] = None
    migrate_from_chat_id: Optional[int] = None
    pinned_message: Optional['Message'] = None
    # invoice: Optional[Invoice] = None
    # successful_payment: Optional[SuccessfulPayment] = None
    connected_website: Optional[str] = None
    # passport_data: Optional[PassportData] = None
    reply_markup: Optional[InlineKeyboardMarkup] = None
    from_user: Optional[User] = field(metadata=config(field_name='from'), default=None)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CallbackQuery:
    callback_query_id: str = field(metadata=config(field_name='id'))
    from_user: User = field(metadata=config(field_name='from'))
    chat_instance: str
    data: Optional[str] = None
    game_short_name: Optional[str] = None
    message: Optional[Message] = None
    inline_message_id: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Update:
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    channel_post: Optional[Message] = None
    edited_channel_post: Optional[Message] = None
    # inline_query: Optional[InlineQuery] = None
    # chosen_inline_result = Optional[ChosenInlineResult] = None
    callback_query: Optional[CallbackQuery] = None
    # shipping_query: Optional[ShippingQuery] = None
    # pre_checkout_query: Optional[PreCheckoutQuery] = None
    # poll: Optional[Poll] = None
    # poll_answer: Optional[PollAnswer] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class WebhookInfo:
    has_custom_certificate: bool
    pending_update_count: int
    url: Optional[str] = None
    ip_address: Optional[str] = None
    last_error_date: Optional[int] = None
    last_error_message: Optional[str] = None
    max_connections: Optional[int] = None
    allowed_updates: Optional[List[str]] = None
