.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo
	@echo 'Targets:'
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "  %-20s %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

# Export Cursor/VS Code configuration
export_config: ## Export VS Code/Cursor configuration
	cursor_setup.sh export

# Import Cursor/VS Code configuration
import_config: ## Import VS Code/Cursor configuration
	cursor_setup.sh import

# Django related commands (local)
makemigrations: ## Run Django makemigrations locally
	python manage.py makemigrations
migrate: ## Run Django migrate locally
	python manage.py migrate

# Django related commands (docker)
docker-migrations: ## Run Django makemigrations in Docker
	docker compose exec web python manage.py makemigrations
docker-migrate: ## Run Django migrate in Docker
	docker compose exec web python manage.py migrate

superuser: ## Create Django superuser in Docker
	docker compose exec web python manage.py createsuperuser

# Docker commands
up: ## Start Docker containers in detached mode
	docker compose -f _setup/docker-compose.yml up -d

down: ## Stop Docker containers
	docker compose -f _setup/docker-compose.yml down

build: ## Build Docker images
	docker compose -f _setup/docker-compose.yml build

buildrun: ## Build Docker images and run containers
	docker compose -f _setup/docker-compose.yml build && docker compose -f _setup/docker-compose.yml up -d

# Docker logs
logs: ## View all Docker container logs
	docker compose -f _setup/docker-compose.yml logs -f

logs-web: ## View web container logs
	docker compose -f _setup/docker-compose.yml logs -f web

logs-celery: ## View celery container logs
	docker compose -f _setup/docker-compose.yml logs -f celery

logs-beat: ## View celery-beat container logs
	docker compose -f _setup/docker-compose.yml logs -f celery-beat

logs-redis: ## View redis container logs
	docker compose -f _setup/docker-compose.yml logs -f redis

ps: ## List running Docker containers
	docker compose -f _setup/docker-compose.yml ps

clean: ## Remove Docker volumes and Python cache files
	docker compose -f _setup/docker-compose.yml down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

restart:
	docker compose -f _setup/docker-compose.yml restart

enter-shell:
	docker compose -f _setup/docker-compose.yml run --rm web bash

install-reqs:
	docker compose -f _setup/docker-compose.yml run --rm web pip install -r _setup/requirements.txt
	docker compose -f _setup/docker-compose.yml run --rm celery pip install -r _setup/requirements.txt
	docker compose -f _setup/docker-compose.yml run --rm celery-beat pip install -r _setup/requirements.txt
	docker compose -f _setup/docker-compose.yml run --rm redis pip install -r _setup/requirements.txt
	pip install -r _setup/requirements.txt
	
