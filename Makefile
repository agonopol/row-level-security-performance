seed-db:
	./init.py --port 5496 && python ./init.py --port 5411

down:
	docker-compose down
up:
	docker-compose up &
