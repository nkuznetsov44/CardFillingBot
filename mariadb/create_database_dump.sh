MYSQL_USER=cardfillingbot
MYSQL_PASSWORD='cardfillingbot'
docker run --rm --network container:cardfillingbot-db mysql:latest mysqldump -h127.0.0.1 -u $MYSQL_USER -p$MYSQL_PASSWORD cardfillingbot --column-statistics=0 > dump.sql

scp $USER@$HOST:~/dump.sql ./mariadb
