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
	docker compose up -d

down: ## Stop Docker containers
	docker compose down

build: ## Build Docker images
	docker compose build

buildrun: ## Build Docker images and run containers
	docker compose build && docker compose up -d

# Docker logs
logs: ## View all Docker container logs
	docker compose logs -f

logs-web: ## View web container logs
	docker compose logs -f web

logs-celery: ## View celery container logs
	docker compose logs -f celery

logs-beat: ## View celery-beat container logs
	docker compose logs -f celery-beat

logs-redis: ## View redis container logs
	docker compose logs -f redis

ps: ## List running Docker containers
	docker compose ps

clean: ## Remove Docker volumes and Python cache files
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

restart:
	docker compose restart

enter-shell:
	docker compose run --rm web bash