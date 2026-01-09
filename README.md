## Run local

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

**Docker:**
```bash
docker-compose up -d
```

**MySQL CLI:**
```bash
docker exec -it cardfillingbot-db mariadb -u root
use CardFillingBot;
```
