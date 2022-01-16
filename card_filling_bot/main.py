import logging
import os
from flask import Flask, request
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from settings import NEED_RESET_WEBHOOK, WEBHOOK_URL, database_uri, scheduler_threads
from card_filling_bot import CardFillingBot, CardFillingBotSettings


# Configuring flask app
class Config:
    SCHEDULER_API_ENABLED = False
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=database_uri)
    }
    SCHEDULER_EXECUTORS = {
        'default': ThreadPoolExecutor(scheduler_threads)
    }
    SCHEDULER_JOB_DEFAULTS = {}
    SCHEDULER_TIMEZONE = 'UTC'


# Creating flask app
app = Flask(__name__)
app.config.from_object(Config())


# Getting gunicorn logger
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(logging.INFO)


# Starting scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
app.logger.info('Started scheduler')


# Starting cardfillingbot
bot_settings = CardFillingBotSettings(
    scheduler=scheduler,
    logger=app.logger
)
bot = CardFillingBot(token=os.getenv('TELEGRAM_TOKEN'), settings=bot_settings)


# Setting webhook if needed
webhook_info = bot.get_webhook_info()
app.logger.info(webhook_info)

need_reset_webhook = NEED_RESET_WEBHOOK or not webhook_info.url or webhook_info.url != WEBHOOK_URL

if need_reset_webhook:
    app.logger.info('Reseting webhook')
    if webhook_info.url:
        bot.delete_webhook()
    bot.set_webhook(url=WEBHOOK_URL)


@app.route('/', methods=['POST'])
def receive_update():
    try:
        update = request.get_json()
        app.logger.info(f'Got update {update}')
        bot.handle_update_raw(update)
        return 'ok'
    except Exception:
        if update:
            app.logger.exception(f'Exception in processing update {update}')
        else:
            app.logger.exception('Unexpected error')
        return 'not ok'
