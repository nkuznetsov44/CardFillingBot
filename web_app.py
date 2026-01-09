import logging
from flask import Flask
from settings import settings
from services.card_fill_service import CardFillService

app = Flask(__name__, template_folder='web/templates')
app.config['SECRET_KEY'] = settings.web_secret_key
app.config['SESSION_TYPE'] = 'filesystem'

app.jinja_env.globals.update(min=min, max=max)

card_fill_service = CardFillService()

logging.basicConfig(level=logging.getLevelName(settings.log_level))
logger = logging.getLogger(__name__)

from web.routes import init_routes
init_routes(app, card_fill_service)

if __name__ == '__main__':
    logger.info(f"Starting web application on {settings.webapp_host}:{settings.webapp_port}")
    app.run(host=settings.webapp_host, port=settings.webapp_port, debug=True)
