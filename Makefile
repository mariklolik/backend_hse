run:
	uvicorn main:app --reload

worker:
	python -m workers.moderation_worker

migrate:
	pgmigrate -c "host=localhost port=5432 dbname=backend user=postgres password=postgres" -d migrations migrate

test:
	pytest -m "not integration"

test-integration:
	pytest -m "integration"

test-all:
	pytest

docker-up:
	docker compose up -d

docker-down:
	docker compose down
