import os

telegram_token = os.getenv('TELEGRAM_TOKEN')

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

scheduler_clear_jobs = int(os.getenv('SCHEDULER_CLEAR_JOBS'))

webhook_host = os.getenv('WEBHOOK_HOST')
webhook_path = os.getenv('WEBHOOK_PATH', '')
webhook_url = f'{webhook_host}/{webhook_path}'

webapp_host = '0.0.0.0'
webapp_port = 8000
