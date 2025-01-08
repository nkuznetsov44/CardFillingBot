Run local

```
python3 -m pip install aiogram emoji marshmallow marshmallow_dataclass matplotlib pymysql redis sqlalchemy prettytable python-dotenv
docker compose -f docker-compose-db.yml up --build -d
python3 card_filling_bot.py --dotenv
```

Get mysql cli inside container

```
docker exec -it cardfillingbot-db mariadb
use cardfillingbot;
```
