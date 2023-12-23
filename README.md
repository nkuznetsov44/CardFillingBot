Run local

`python3 -m pip install aiogram emoji marshmallow marshmallow_dataclass matplotlib pymysql redis sqlalchemy prettytable`
`docker compose -f docker-compose-db.yml up --build -d`

```
export TELEGRAM_TOKEN=""
export MYSQL_HOST="localhost"
export MYSQL_DATABASE="cardfillingbot"
export MYSQL_USER="cardfillingbot"
export MYSQL_PASSWORD="cardfillingbot"
export REDIS_PASSWORD="cardfillingbot"
export LOG_LEVEL="DEBUG"
```
