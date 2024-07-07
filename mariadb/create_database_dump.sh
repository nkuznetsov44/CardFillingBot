# mysqldump -h 192.168.88.101 -u root -p --no-data --column-statistics=0 CardFillingBot > CardFillingBot-1-schema.sql
# mysqldump -h 192.168.88.101 -u root -p --column-statistics=0 CardFillingBot > CardFillingBot-0-dumpwithdata.sql
MYSQL_USER=cardfillingbot
MYSQL_PASSWORD='cardfillingbot'
docker run --rm --network container:cardfillingbot-db mysql:latest mysqldump -h127.0.0.1 -u $MYSQL_USER -p$MYSQL_PASSWORD cardfillingbot --column-statistics=0 > dump.sql
