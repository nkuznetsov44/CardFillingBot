from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
import json
import requests
from telegramapi.types import Update, Message, User, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode, WebhookInfo


class TelegramBotException(Exception):
    pass


class TelegramApiException(TelegramBotException):
    def __init__(self, *args, error_code: Optional[int] = None, description: Optional[str] = None) -> None:
        super(TelegramApiException, self).__init__(*args)
        self.error_code = error_code
        self.description = description

    def __repr__(self) -> str:
        return (
            super(TelegramApiException, self).__repr__() +
            f'\nErrorCode: "{self.error_code}"\nDescription: "{self.description}"'
        )

    def __str__(self):
        return self.__repr__()


ChatId = Union[int, str]
ReplyMarkup = Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]]
MessageHandlerFunc = Callable[['Bot', Message], None]
CallbackQueryHandlerFunc = Callable[['Bot', CallbackQuery], None]


T = TypeVar('T')


class Handler(Generic[T], ABC):
    def __init__(self, handler_func: Callable[['Bot', T], None], **kwargs: Any):
        self.__handler_func = handler_func

    @abstractmethod
    def should_handle(self, obj: T) -> bool:
        """Returns True if an object should be handled by this handler"""

    def handle(self, bot_instance: 'Bot', obj: T) -> None:
        self.__handler_func(bot_instance, obj)


class MessageHandler(Handler[Message]):
    def __init__(self, handler_func: MessageHandlerFunc, commands: Optional[List[str]] = None) -> None:
        super().__init__(handler_func)
        self.__handler_func = handler_func
        self.__commands = commands

    def should_handle(self, message: Message) -> bool:
        return (
            not self.__commands or
            not message.text or
            any(message.text.startswith(f'/{command}') for command in self.__commands)
        )


def message_handler(commands: Optional[List[str]] = None) -> Callable[[MessageHandlerFunc], MessageHandler]:
    def wrapper(handler_func: MessageHandlerFunc) -> MessageHandler:
        return MessageHandler(handler_func, commands=commands)
    return wrapper


class CallbackQueryHandler(Handler[CallbackQuery]):
    def __init__(self, handler_func: CallbackQueryHandlerFunc, accepted_data: Optional[List[str]] = None) -> None:
        super().__init__(handler_func)
        self.__handler_func = handler_func
        self.__accepted_data = accepted_data

    def should_handle(self, callback_query: CallbackQuery) -> bool:
        return (
            not self.__accepted_data or
            not callback_query.data or
            any(callback_query.data and callback_query.data.startswith(cqd) for cqd in self.__accepted_data)
        )


def callback_query_handler(accepted_data: Optional[List[str]] = None) -> Callable[[CallbackQueryHandlerFunc], CallbackQueryHandler]:
    def wrapper(handler_func: CallbackQueryHandlerFunc) -> CallbackQueryHandler:
        return CallbackQueryHandler(handler_func, accepted_data=accepted_data)
    return wrapper


class BotMeta(type):
    def __new__(mcs, name, bases, attrs):
        message_handlers = attrs['_message_handlers'] = list()
        callback_query_handlers = attrs['_callback_query_handlers'] = list()

        # inherit bases handlers
        for base in bases:
            message_handlers.extend(getattr(base, '_message_handlers'))
            callback_query_handlers.extend(getattr(base, '_callback_query_handlers'))

        for attr in attrs.values():
            if isinstance(attr, MessageHandler):
                message_handlers.append(attr)
            elif isinstance(attr, CallbackQueryHandler):
                callback_query_handlers.append(attr)

        return type.__new__(mcs, name, bases, attrs)


class Bot(metaclass=BotMeta):
    def __init__(
        self,
        token: str
    ) -> None:
        self.token = token
        self.url = 'https://api.telegram.org/bot' + token + '/'
        self.last_update_id = None

    @property
    def message_handlers(self) -> List[Handler[Message]]:
        """This message_handlers property is initialized by metaclass"""
        return getattr(self, '_message_handlers')

    @property
    def callback_query_handlers(self) -> List[Handler[CallbackQuery]]:
        """This callback_query_handlers property is initialized by metaclass"""
        return getattr(self, '_callback_query_handlers')

    def long_polling(self, timeout: int = 30) -> None:
        while 1 == 1:
            offset = None
            if self.last_update_id:
                offset = self.last_update_id + 1
            updates = self.get_updates(offset=offset, timeout=timeout)
            if updates:
                self.handle_updates(updates)

    def get_webhook_info(self):
        response = self._make_request('getWebhookInfo')
        return WebhookInfo.schema().load(response, many=False)

    def delete_webhook(self, drop_pending_updates: Optional[bool] = None):
        response = self._make_request('deleteWebhook')
        if not response:
            raise TelegramApiException(f'Failed to delete webhook {response}')

    def set_webhook(
        self,
        url: str,
        certificate: Optional[Any] = None,
        ip_address: Optional[str] = None,
        max_connections: Optional[int] = None,
        allowed_updates: Optional[List[str]] = None,
        drop_pending_updates: Optional[bool] = None
    ):
        files = None
        if certificate:
            files = {'certificate': certificate}
        params = {
            'url': url,
            'ip_address': ip_address,
            'max_connections': max_connections,
            'allowed_updates': allowed_updates,
            'drop_pending_updates': drop_pending_updates
        }
        response = self._make_request('setWebhook', params=params)
        if not response == True:
            raise TelegramApiException(f'Failed to set webhook {response}')

    def handle_updates(self, updates: List[Update]) -> None:
        for update in updates:
            if update.message:
                self.handle_message(update.message)
            elif update.callback_query:
                self.handle_callback_query(update.callback_query)

    def handle_update_raw(self, update_raw: Dict[str, Any]) -> None:
        update = Update.schema().load(update_raw, many=False)
        self.handle_updates([update])

    def handle_message(self, message: Message) -> None:
        message_was_handled = False
        for handler in self.message_handlers:
            if handler.should_handle(message):
                handler.handle(self, message)
                message_was_handled = True
        if not message_was_handled:
            raise TelegramBotException(
                f'Message {Message} was not handled because no suitable message handler was provided.'
            )

    def handle_callback_query(self, callback_query: CallbackQuery) -> None:
        callback_query_was_handled = False
        for handler in self.callback_query_handlers:
            if handler.should_handle(callback_query):
                handler.handle(self, callback_query)
                callback_query_was_handled = True
        if not callback_query_was_handled:
            raise TelegramBotException(
                f'Callback query {CallbackQuery} was not handled'
                'because no suitable callback query handler was provided.'
            )

    @staticmethod
    def _check_response(response: requests.Response) -> Any:
        if response.status_code != requests.codes.ok:
            error_code = None
            description = None
            try:
                response_json = response.json()
                error_code = response_json['error_code'],
                description = response_json['description']
            except Exception:
                pass
            raise TelegramApiException(
                f'Got status code {response.status_code}: {response.reason}\n{response.text.encode("utf8")}',
                error_code=error_code,
                description=description
            )

        try:
            response_json = response.json()
        except json.JSONDecodeError as jde:
            raise TelegramApiException(f'Got invalid json\n{response.text.encode("utf8")}', jde)

        try:
            if not response_json['ok']:
                raise TelegramApiException(
                    error_code=response_json['error_code'],
                    description=response_json['description']
                )
            return response_json['result']
        except KeyError as ke:
            raise TelegramApiException(f'Got unexpected json\n{response_json}', ke)

    def _make_request(
        self,
        api_method: str,
        http_method: Optional[str] = 'get',
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None
    ) -> Any:
        if http_method == 'get':
            response = requests.get(self.url + api_method, params=params, files=files)
        elif http_method == 'post':
            response = requests.post(self.url + api_method, data=params, files=files)
        else:
            raise TelegramApiException(f'Unsupported http method {http_method}')
        return self._check_response(response)

    def get_me(self) -> User:
        return User.from_dict(self._make_request('getMe'))

    def get_updates(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
        allowed_updates: Optional[List[str]] = None
    ) -> List[Update]:
        params = {
            'offset': offset,
            'limit': limit,
            'timeout': timeout,
            'allowed_updates': allowed_updates
        }
        result = self._make_request('getUpdates', params=params)
        if len(result) > 0:
            updates = Update.schema().load(result, many=True)
            self.last_update_id = updates[-1].update_id
            return updates

    def send_message(
        self,
        chat_id: ChatId,
        text: str,
        parse_mode: Optional[ParseMode] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[ReplyMarkup] = None
    ) -> Message:
        params = {
            'chat_id': chat_id,
            'text': text,
            'disable_web_page_preview': disable_web_page_preview,
            'disable_notification': disable_notification,
            'reply_to_message_id': reply_to_message_id,
        }
        if reply_markup:
            params['reply_markup'] = reply_markup.to_json(allow_nan=False)
        if parse_mode:
            params['parse_mode'] = parse_mode.value
        result = self._make_request('sendMessage', http_method='post', params=params)
        return Message.from_dict(result)

    def send_chat_action(self, chat_id: ChatId, action: str) -> bool:
        params = {
            'chat_id': chat_id,
            'action': action
        }
        return self._make_request('sendChatAction', params=params)

    def send_photo(
        self,
        chat_id: ChatId,
        photo: bytes,
        caption: Optional[str] = None,
        parse_mode: Optional[ParseMode] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[ReplyMarkup] = None
    ) -> Message:
        files = {'photo': photo}
        params = {
            'chat_id': chat_id,
            'caption': caption,
            'disable_notification': disable_notification,
            'reply_to_message_id': reply_to_message_id,
        }
        if reply_markup:
            params['reply_markup'] = reply_markup.to_json(allow_nan=False)
        if parse_mode:
            params['parse_mode'] = parse_mode.value
        result = self._make_request('sendPhoto', http_method='post', params=params, files=files)
        return Message.from_dict(result)
