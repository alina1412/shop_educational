run:
	poetry run python -m service


ifdef OS
	docker_up = docker compose up -d
	docker_down = docker compose down --volumes
else
	docker_up = sudo docker-compose up -d
	docker_down = sudo docker-compose down
endif

up:
	$(docker_up) 

alembic:
	$(alembic_up)

down:
	$(docker_down)

test-empty:
	make renew
	poetry run pytest -m my --verbosity=2 --showlocals --cov=service --cov-report html

renew:
	poetry run alembic -c alembic.ini downgrade -1
	poetry run alembic -c alembic.ini upgrade head

test-all:
	poetry run pytest -vsx --verbosity=2

alembic-gen:
	alembic revision -m "edit" --head schema@head

alembic-up:
	alembic -c alembic.ini upgrade schema@head 

alembic-data:
	alembic -c alembic.ini upgrade data@head

alembic-down:
	alembic -c alembic.ini downgrade -1

lint:
	poetry run black service
	poetry run pylint service
	poetry run black tests
	poetry run pylint tests

isort:
	poetry run isort service tests

req:
	poetry export -f requirements.txt --without-hashes --with dev --output ./service/requirements.txt

format:
	ruff format .
	ruff check --fix