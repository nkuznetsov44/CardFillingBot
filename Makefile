start_db:
	docker compose -f docker-compose-db.yml up --build -d

dbcli:
	docker exec -it cardfillingbot-db mariadb cardfillingbot

run:
	python3 card_filling_bot.py --dotenv
