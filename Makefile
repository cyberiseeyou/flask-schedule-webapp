# Flask Schedule WebApp - Docker Makefile

.PHONY: help build up down restart logs shell test clean backup

# Default target
help:
	@echo "Flask Schedule WebApp - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo "  build          - Build Docker images"
	@echo "  up             - Start services in background"
	@echo "  down           - Stop and remove containers"
	@echo "  restart        - Restart all services"
	@echo "  logs           - View application logs"
	@echo "  shell          - Access container shell"
	@echo "  test           - Run test suite"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  migrate        - Run database migrations"
	@echo "  init-db        - Initialize database"
	@echo "  backup         - Backup database"
	@echo "  clean          - Remove containers, volumes, and images"
	@echo "  dev            - Start in development mode"
	@echo "  prod           - Start in production mode"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "Application running at http://localhost:8135"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f web

# Access container shell
shell:
	docker-compose exec web bash

# Run tests
test:
	docker-compose exec web pytest -v

# Run tests with coverage
test-cov:
	docker-compose exec web pytest --cov=scheduler_app --cov-report=html

# Run database migrations
migrate:
	docker-compose exec web flask db upgrade

# Initialize database
init-db:
	docker-compose exec web python -c "from scheduler_app.app import init_db; init_db()"

# Backup database
backup:
	@mkdir -p backups
	docker-compose exec web cp /app/scheduler_app/instance/scheduler.db /app/backups/scheduler_$$(date +%Y%m%d_%H%M%S).db
	@echo "Database backed up to backups/"

# Clean everything
clean:
	docker-compose down -v --rmi all --remove-orphans
	@echo "All containers, volumes, and images removed"

# Development mode
dev:
	@echo "FLASK_ENV=development" > docker-compose.override.yml
	@echo "FLASK_DEBUG=1" >> docker-compose.override.yml
	docker-compose up

# Production mode
prod:
	@rm -f docker-compose.override.yml
	docker-compose up -d
	@echo "Production mode: http://localhost:8135"

# Setup environment
setup:
	@if [ ! -f .env ]; then \
		cp .env.docker .env; \
		echo ".env file created - please update with your credentials"; \
	else \
		echo ".env file already exists"; \
	fi

# Generate secret keys
generate-keys:
	@echo "SECRET_KEY=$$(python -c 'import secrets; print(secrets.token_hex(32))')"
	@echo "SETTINGS_ENCRYPTION_KEY=$$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
