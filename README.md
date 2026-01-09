# CardFillingBot

Telegram bot for tracking personal expenses with web interface.

## Production Deployment

### Required .env variables

```bash
WEB_DEV_MODE=false
WEB_SECRET_KEY=your-secret-key  # python3 -c "import secrets; print(secrets.token_hex(32))"
TELEGRAM_BOT_USERNAME=YourBot_bot
TELEGRAM_TOKEN=your-bot-token
ADMIN_USER_ID=123456789
MYSQL_HOST=mariadb
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_DATABASE=database
LOG_LEVEL=INFO
TZ=Europe/Moscow
```

### Start

```bash
docker compose up -d
```

### Rebuild and restart webui

```bash
docker compose down webui
docker compose build --no-cache webui
docker compose up -d webui
```

### Check logs

```bash
docker compose logs -f webui
```

### SSL Setup

```bash
./init-letsencrypt.sh
```

## Local Development

**Bot:**
```bash
pip install -r requirements.txt
docker compose -f docker-compose-db.yml up -d
python3 card_filling_bot.py --dotenv
```

**Web Interface:**
```bash
python3 web_app.py --dotenv
```

**MySQL CLI:**
```bash
docker exec -it cardfillingbot-db mariadb -u root
use CardFillingBot;
```
