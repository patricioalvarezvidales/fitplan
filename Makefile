.PHONY: init up down logs test lint build clean

init:
	cp -n .env.example .env || true
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose run --rm api pytest

lint:
	docker compose run --rm api ruff check app tests
	docker compose run --rm web npm run lint

build:
	docker compose build

clean:
	docker compose down -v --remove-orphans
