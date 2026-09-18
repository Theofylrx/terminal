# Terminal Trading System - Makefile
# Simplifies common development tasks

.PHONY: help build up down logs test clean init-db

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m  # No Color

help: ## Show this help message
	@echo '$(CYAN)Terminal Trading System - Available Commands:$(NC)'
	@echo ''
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==================== SETUP ====================

dev-setup: ## First-time setup for development
	@echo '$(CYAN)Setting up Terminal trading system...$(NC)'
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo '$(YELLOW)Created .env file from .env.example$(NC)'; \
		echo '$(RED)⚠️  Please edit .env with your API keys before continuing$(NC)'; \
	else \
		echo '$(GREEN).env file already exists$(NC)'; \
	fi
	@echo '$(CYAN)Building Docker images...$(NC)'
	@docker-compose build
	@echo '$(CYAN)Starting services...$(NC)'
	@docker-compose up -d
	@echo '$(YELLOW)Waiting for database to be ready...$(NC)'
	@sleep 10
	@echo '$(CYAN)Initializing database...$(NC)'
	@make init-db
	@echo '$(GREEN)✓ Setup complete!$(NC)'
	@echo ''
	@echo 'Services:'
	@echo '  - Frontend:    http://localhost:3000'
	@echo '  - API Gateway: http://localhost:8080'
	@echo '  - Grafana:     http://localhost:3001'
	@echo '  - RabbitMQ:    http://localhost:15672'

# ==================== DOCKER ====================

build: ## Build all Docker images
	@echo '$(CYAN)Building Docker images...$(NC)'
	@docker-compose build

up: ## Start all services
	@echo '$(CYAN)Starting all services...$(NC)'
	@docker-compose up -d
	@echo '$(GREEN)✓ All services started$(NC)'

down: ## Stop all services
	@echo '$(CYAN)Stopping all services...$(NC)'
	@docker-compose down
	@echo '$(GREEN)✓ All services stopped$(NC)'

restart: ## Restart all services
	@echo '$(CYAN)Restarting all services...$(NC)'
	@docker-compose restart
	@echo '$(GREEN)✓ All services restarted$(NC)'

ps: ## Show running containers
	@docker-compose ps

# ==================== LOGS ====================

logs: ## Show logs from all services
	@docker-compose logs -f

logs-service: ## Show logs for specific service (make logs-service SERVICE=trading-service)
	@if [ -z "$(SERVICE)" ]; then \
		echo '$(RED)Error: SERVICE not specified$(NC)'; \
		echo 'Usage: make logs-service SERVICE=trading-service'; \
	else \
		docker-compose logs -f $(SERVICE); \
	fi

logs-gateway: ## Show API Gateway logs
	@docker-compose logs -f gateway

logs-trading: ## Show Trading Service logs
	@docker-compose logs -f trading-service

logs-market-data: ## Show Market Data Service logs
	@docker-compose logs -f market-data-service

logs-technical: ## Show Technical Analyst logs
	@docker-compose logs -f technical-analyst-service

logs-executor: ## Show Executor Service logs
	@docker-compose logs -f executor-service

# ==================== SERVICE MANAGEMENT ====================

restart-service: ## Restart specific service (make restart-service SERVICE=trading-service)
	@if [ -z "$(SERVICE)" ]; then \
		echo '$(RED)Error: SERVICE not specified$(NC)'; \
		echo 'Usage: make restart-service SERVICE=trading-service'; \
	else \
		echo '$(CYAN)Restarting $(SERVICE)...$(NC)'; \
		docker-compose restart $(SERVICE); \
		echo '$(GREEN)✓ $(SERVICE) restarted$(NC)'; \
	fi

shell-service: ## Open shell in service (make shell-service SERVICE=trading-service)
	@if [ -z "$(SERVICE)" ]; then \
		echo '$(RED)Error: SERVICE not specified$(NC)'; \
		echo 'Usage: make shell-service SERVICE=trading-service'; \
	else \
		docker-compose exec $(SERVICE) /bin/bash || docker-compose exec $(SERVICE) /bin/sh; \
	fi

scale-service: ## Scale service (make scale-service SERVICE=technical-analyst-service REPLICAS=3)
	@if [ -z "$(SERVICE)" ] || [ -z "$(REPLICAS)" ]; then \
		echo '$(RED)Error: SERVICE or REPLICAS not specified$(NC)'; \
		echo 'Usage: make scale-service SERVICE=technical-analyst-service REPLICAS=3'; \
	else \
		docker-compose up -d --scale $(SERVICE)=$(REPLICAS); \
	fi

# ==================== DATABASE ====================

db-shell: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB

init-db: ## Initialize database with schema
	@echo '$(CYAN)Initializing database...$(NC)'
	@docker-compose exec -T postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
	@echo '$(GREEN)✓ TimescaleDB extension created$(NC)'
	@echo '$(YELLOW)Run migrations to create tables$(NC)'

migrate-up: ## Run database migrations (upgrade)
	@echo '$(CYAN)Running database migrations...$(NC)'
	@docker-compose exec backend-api alembic upgrade head
	@echo '$(GREEN)✓ Migrations complete$(NC)'

migrate-down: ## Rollback last migration
	@echo '$(CYAN)Rolling back last migration...$(NC)'
	@docker-compose exec backend-api alembic downgrade -1

migrate-create: ## Create new migration (make migrate-create MESSAGE="add users table")
	@if [ -z "$(MESSAGE)" ]; then \
		echo '$(RED)Error: MESSAGE not specified$(NC)'; \
		echo 'Usage: make migrate-create MESSAGE="add users table"'; \
	else \
		docker-compose exec backend-api alembic revision --autogenerate -m "$(MESSAGE)"; \
	fi

db-reset: ## ⚠️  DANGER: Drop and recreate database
	@echo '$(RED)⚠️  WARNING: This will DELETE ALL DATA!$(NC)'
	@echo -n 'Are you sure? [y/N] ' && read ans && [ $${ans:-N} = y ]
	@docker-compose down -v
	@docker-compose up -d postgres redis
	@sleep 5
	@make init-db
	@echo '$(GREEN)✓ Database reset complete$(NC)'

# ==================== REDIS ====================

redis-cli: ## Open Redis CLI
	@docker-compose exec redis redis-cli

redis-flush: ## ⚠️  Clear all Redis data
	@echo '$(YELLOW)Flushing Redis...$(NC)'
	@docker-compose exec redis redis-cli FLUSHALL
	@echo '$(GREEN)✓ Redis flushed$(NC)'

# ==================== TESTING ====================

test: ## Run all tests
	@echo '$(CYAN)Running tests...$(NC)'
	@docker-compose exec backend-api pytest
	@docker-compose exec trading-service pytest
	@docker-compose exec technical-analyst-service pytest

test-unit: ## Run unit tests only
	@echo '$(CYAN)Running unit tests...$(NC)'
	@docker-compose exec backend-api pytest tests/unit -v

test-integration: ## Run integration tests
	@echo '$(CYAN)Running integration tests...$(NC)'
	@docker-compose exec backend-api pytest tests/integration -v

test-service: ## Run tests for specific service (make test-service SERVICE=trading-service)
	@if [ -z "$(SERVICE)" ]; then \
		echo '$(RED)Error: SERVICE not specified$(NC)'; \
		echo 'Usage: make test-service SERVICE=trading-service'; \
	else \
		docker-compose exec $(SERVICE) pytest -v; \
	fi

test-coverage: ## Run tests with coverage report
	@echo '$(CYAN)Running tests with coverage...$(NC)'
	@docker-compose exec backend-api pytest --cov=. --cov-report=html
	@echo '$(GREEN)✓ Coverage report generated in htmlcov/$(NC)'

# ==================== MONITORING ====================

monitor: ## Open Grafana dashboard
	@echo '$(CYAN)Opening Grafana...$(NC)'
	@open http://localhost:3001 || xdg-open http://localhost:3001 || echo 'Visit http://localhost:3001'

prometheus: ## Open Prometheus UI
	@echo '$(CYAN)Opening Prometheus...$(NC)'
	@open http://localhost:9090 || xdg-open http://localhost:9090 || echo 'Visit http://localhost:9090'

rabbitmq: ## Open RabbitMQ Management UI
	@echo '$(CYAN)Opening RabbitMQ Management...$(NC)'
	@open http://localhost:15672 || xdg-open http://localhost:15672 || echo 'Visit http://localhost:15672'

# ==================== HEALTH CHECKS ====================

health: ## Check health of all services
	@echo '$(CYAN)Checking service health...$(NC)'
	@echo -n 'API Gateway:          '
	@curl -sf http://localhost:8080/health > /dev/null && echo '$(GREEN)✓ UP$(NC)' || echo '$(RED)✗ DOWN$(NC)'
	@echo -n 'Trading Service:      '
	@curl -sf http://localhost:8001/health > /dev/null && echo '$(GREEN)✓ UP$(NC)' || echo '$(RED)✗ DOWN$(NC)'
	@echo -n 'Market Data Service:  '
	@curl -sf http://localhost:8002/health > /dev/null && echo '$(GREEN)✓ UP$(NC)' || echo '$(RED)✗ DOWN$(NC)'

# ==================== DATA ====================

backfill-data: ## Backfill historical market data
	@echo '$(CYAN)Backfilling market data...$(NC)'
	@docker-compose exec market-data-service python scripts/backfill_data.py
	@echo '$(GREEN)✓ Backfill complete$(NC)'

# ==================== CLEANUP ====================

clean: ## Remove all containers, volumes, and images
	@echo '$(RED)⚠️  This will remove all containers, volumes, and images$(NC)'
	@echo -n 'Are you sure? [y/N] ' && read ans && [ $${ans:-N} = y ]
	@docker-compose down -v --rmi all
	@echo '$(GREEN)✓ Cleanup complete$(NC)'

clean-volumes: ## Remove all volumes (data will be lost)
	@echo '$(RED)⚠️  This will DELETE ALL DATA$(NC)'
	@echo -n 'Are you sure? [y/N] ' && read ans && [ $${ans:-N} = y ]
	@docker-compose down -v
	@echo '$(GREEN)✓ Volumes removed$(NC)'

# ==================== DEVELOPMENT ====================

format: ## Format code with black and isort
	@echo '$(CYAN)Formatting code...$(NC)'
	@docker-compose exec backend-api black .
	@docker-compose exec backend-api isort .
	@echo '$(GREEN)✓ Code formatted$(NC)'

lint: ## Lint code with flake8 and mypy
	@echo '$(CYAN)Linting code...$(NC)'
	@docker-compose exec backend-api flake8 .
	@docker-compose exec backend-api mypy .

# ==================== PRODUCTION ====================

prod-build: ## Build production images
	@echo '$(CYAN)Building production images...$(NC)'
	@docker-compose -f docker-compose.prod.yml build

prod-up: ## Start production stack
	@echo '$(CYAN)Starting production stack...$(NC)'
	@docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production stack
	@docker-compose -f docker-compose.prod.yml down
