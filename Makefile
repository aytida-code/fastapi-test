.PHONY: up down logs migrate test lint

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f

migrate:
	docker compose exec app alembic upgrade head

test:
	pytest -v

lint:
	ruff check app tests
