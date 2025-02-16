from typing import Optional
import os
from entities import AppMode
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--dotenv', action='store_true')
args = parser.parse_args()

if args.dotenv:
    from dotenv import load_dotenv
    load_dotenv()
    print('Loaded dotenv', f'{os.environ}')


class _Settings:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")

        self.mysql_user = os.getenv("MYSQL_USER")
        self.mysql_password = os.getenv("MYSQL_PASSWORD")
        self.mysql_host = os.getenv("MYSQL_HOST")
        self.mysql_database = os.getenv("MYSQL_DATABASE")

        self.redis_host = os.getenv("REDIS_HOST")
        self.redis_port = 6379
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD")

        self.webhook_host = os.getenv("WEBHOOK_HOST")
        self.webhook_path = os.getenv("WEBHOOK_PATH", "/")

        self.webapp_host = os.getenv("WEBAPP_HOST", "0.0.0.0")
        self.webapp_port = int(os.getenv("WEBAPP_PORT", "8000"))

        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        self.app_mode = AppMode(os.getenv("APP_MODE", "POLLING"))

    @classmethod
    def _maybe_int(cls, val: Optional[str]) -> Optional[int]:
        if val is None:
            return None
        return int(val)

    @classmethod
    def _any_none(cls, *vals: Any) -> bool:
        return any(map(lambda v: v is None, vals))

    @property
    def database_uri(self) -> str:
        if self._any_none(self.mysql_host, self.mysql_database, self.mysql_user, self.mysql_password):
            raise ValueError('Database settings not defined')
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}" f"@{self.mysql_host}/{self.mysql_database}"

    @property
    def webhook_url(self) -> str:
        if self._any_none(self.webhook_host, self.webhook_port):
            raise ValueError('Webhook settings not defined')
        return f"{self.webhook_host}{self.webhook_path}"


settings = _Settings()
