import os


mysql_user = os.getenv('MYSQL_USER')
mysql_password = os.getenv('MYSQL_PASSWORD')
mysql_host = os.getenv('MYSQL_HOST')
mysql_database = os.getenv('MYSQL_DATABASE')

database_uri = (
    f'mysql+pymysql://{mysql_user}:{mysql_password}'
    f'@{mysql_host}/{mysql_database}'
)

redis_host = os.getenv('REDIS_HOST')
redis_port = 6379
redis_db = int(os.getenv('REDIS_DB'))
redis_password = os.getenv('REDIS_PASSWORD')

minor_proportion_user_id = int(os.getenv('MINOR_PROPORTION_USER_ID'))
major_proportion_user_id = int(os.getenv('MAJOR_PROPORTION_USER_ID'))

scheduler_threads = 1

NEED_RESET_WEBHOOK = bool(os.getenv('NEED_RESET_WEBHOOK', False))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
if not WEBHOOK_URL:
    raise Exception('Environment variable WEBHOOK_URL is not set')

host_exposed_port = os.getenv('HOST_EXPOSED_PORT')
