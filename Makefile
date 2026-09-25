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

# ==================== EXECUTOR SERVICE ====================

logs-executor: ## Show Executor Service logs
	@docker-compose logs -f executor-service

logs-auto-trading: ## Show Auto-Trading Engine logs
	@docker-compose logs -f auto-trading-engine

restart-executor: ## Restart Executor Service
	@echo '$(CYAN)Restarting Executor Service...$(NC)'
	@docker-compose restart executor-service
	@echo '$(GREEN)✓ Executor Service restarted$(NC)'

# ==================== SYSTEM STATUS ====================

status: ## Show comprehensive system status
	@echo '$(CYAN)═══════════════════════════════════════════════════════════$(NC)'
	@echo '$(CYAN)            TERMINAL AI TRADING SYSTEM STATUS              $(NC)'
	@echo '$(CYAN)═══════════════════════════════════════════════════════════$(NC)'
	@echo ''
	@echo '$(YELLOW)📊 DOCKER SERVICES:$(NC)'
	@docker-compose ps 2>&1 | grep -v warning | grep -E "terminal-" | awk '{printf "  %-25s %s\n", $$1, $$NF}'
	@echo ''
	@echo '$(YELLOW)🌐 SERVICE HEALTH:$(NC)'
	@printf "  %-30s " "Executor Service (8007):"; \
		curl -sf http://localhost:8007/api/v1/health | jq -r '.status' 2>/dev/null && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)'
	@printf "  %-30s " "Auto-Trading Engine (8005):"; \
		curl -sf http://localhost:8005/health | jq -r '.status' 2>/dev/null && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)'
	@printf "  %-30s " "Market Data Service (8003):"; \
		curl -sf http://localhost:8003/health | jq -r '.status' 2>/dev/null && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)'
	@printf "  %-30s " "Gateway (8080):"; \
		curl -sf http://localhost:8080/health | jq -r '.status' 2>/dev/null && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)'
	@printf "  %-30s " "Auth Service (8001):"; \
		curl -sf http://localhost:8001/health | jq -r '.status' 2>/dev/null && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)'
	@printf "  %-30s " "Trading Service (8002):"; \
		curl -sf http://localhost:8002/health | jq -r '.status' 2>/dev/null && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)'
	@echo ''
	@echo '$(YELLOW)🔗 BROKER CONNECTIONS:$(NC)'
	@curl -sf http://localhost:8007/status 2>/dev/null | jq -r '.brokers | to_entries[] | "  \(.key | ascii_upcase): connected=\(.value.connected)"' || echo '  Could not fetch broker status'
	@echo ''
	@echo '$(YELLOW)📍 ACCESS URLS:$(NC)'
	@echo '  🎨 Frontend:              http://localhost:3000'
	@echo '  📊 API Gateway:           http://localhost:8080'
	@echo '  📈 Grafana:               http://localhost:3001'
	@echo '  🔍 Prometheus:            http://localhost:9090'
	@echo '  🐰 RabbitMQ:              http://localhost:15672'
	@echo ''
	@echo '$(YELLOW)📚 API DOCUMENTATION:$(NC)'
	@echo '  Executor Service:         http://localhost:8007/docs'
	@echo '  Auto-Trading Engine:      http://localhost:8005/docs'
	@echo '  Market Data Service:      http://localhost:8003/docs'
	@echo ''

# ==================== QUICK ACCESS ====================

ui: ## Open Frontend UI in browser
	@echo '$(CYAN)Opening Frontend UI...$(NC)'
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo 'Visit http://localhost:3000'

docs-executor: ## Open Executor Service API docs
	@open http://localhost:8007/docs || xdg-open http://localhost:8007/docs || echo 'Visit http://localhost:8007/docs'

docs-auto-trading: ## Open Auto-Trading Engine API docs
	@open http://localhost:8005/docs || xdg-open http://localhost:8005/docs || echo 'Visit http://localhost:8005/docs'

# ==================== TRADING PIPELINE ====================

start-trading: ## Start complete trading pipeline
	@echo '$(CYAN)Starting complete trading pipeline...$(NC)'
	@docker-compose up -d postgres redis rabbitmq
	@echo '$(YELLOW)Waiting for infrastructure...$(NC)'
	@sleep 5
	@docker-compose up -d market-data-service executor-service trading-service auto-trading-engine
	@echo '$(GREEN)✓ Trading pipeline started$(NC)'
	@make status

stop-trading: ## Stop trading services (keep infrastructure)
	@echo '$(CYAN)Stopping trading services...$(NC)'
	@docker-compose stop auto-trading-engine executor-service market-data-service trading-service
	@echo '$(GREEN)✓ Trading services stopped$(NC)'

test-executor: ## Test Executor Service with sample order
	@echo '$(CYAN)Testing Executor Service...$(NC)'
	@echo '$(YELLOW)Testing position sizing...$(NC)'
	@curl -X POST http://localhost:8007/api/v1/position-size \
		-H "Content-Type: application/json" \
		-d '{"user_id":"test","symbol":"AAPL","entry_price":150.0,"stop_loss_price":145.0,"risk_per_trade_percent":1.0,"method":"fixed_risk"}' \
		| jq .
	@echo ''
	@echo '$(YELLOW)Testing risk check...$(NC)'
	@curl -X POST http://localhost:8007/api/v1/risk-check \
		-H "Content-Type: application/json" \
		-d '{"user_id":"test","symbol":"AAPL","side":"BUY","quantity":10.0,"entry_price":150.0,"stop_loss_price":145.0}' \
		| jq .

# ==================== QUICK START ====================

start-all: ## Start ALL services including frontend
	@echo '$(CYAN)Starting ALL services...$(NC)'
	@docker-compose up -d
	@echo '$(GREEN)✓ All Docker services started$(NC)'
	@echo '$(YELLOW)Note: Frontend runs natively on port 3000$(NC)'
	@sleep 5
	@make status

quick-start: ## Quick start (infrastructure + core trading)
	@echo '$(CYAN)Quick starting Terminal...$(NC)'
	@docker-compose up -d postgres redis rabbitmq gateway auth-service trading-service
	@docker-compose up -d market-data-service executor-service auto-trading-engine
	@echo '$(GREEN)✓ Core services started$(NC)'
	@sleep 3
	@make status

