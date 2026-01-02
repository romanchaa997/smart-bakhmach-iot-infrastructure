.PHONY: help build up down restart logs clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services started. Access API Gateway at http://localhost:8000"

down: ## Stop all services
	docker-compose down

restart: down up ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API Gateway logs
	docker-compose logs -f api-gateway

logs-energy: ## View Energy Service logs
	docker-compose logs -f energy-service

logs-water: ## View Water Service logs
	docker-compose logs -f water-service

logs-transport: ## View Transport Service logs
	docker-compose logs -f transport-service

logs-air: ## View Air Quality Service logs
	docker-compose logs -f air-quality-service

logs-ml: ## View ML Analytics Service logs
	docker-compose logs -f ml-analytics-service

clean: ## Remove all containers, volumes, and images
	docker-compose down -v
	docker system prune -f

test: ## Run tests
	pytest tests/ --cov=services --cov-report=html

lint: ## Run linter
	flake8 services/ shared/ --exclude=venv,env,.git,__pycache__ --max-line-length=127

format: ## Format code with black
	black services/ shared/

db-backup: ## Backup database
	docker-compose exec postgres pg_dump -U iotuser iot_platform > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backup_$$(date +%Y%m%d_%H%M%S).sql"

db-restore: ## Restore database (usage: make db-restore FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "Usage: make db-restore FILE=backup.sql"; exit 1; fi
	docker-compose exec -T postgres psql -U iotuser iot_platform < $(FILE)
	@echo "Database restored from $(FILE)"

db-shell: ## Open database shell
	docker-compose exec postgres psql -U iotuser iot_platform

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "API Gateway: DOWN"
	@curl -s http://localhost:8001/health | jq . || echo "Energy Service: DOWN"
	@curl -s http://localhost:8002/health | jq . || echo "Water Service: DOWN"
	@curl -s http://localhost:8003/health | jq . || echo "Transport Service: DOWN"
	@curl -s http://localhost:8004/health | jq . || echo "Air Quality Service: DOWN"
	@curl -s http://localhost:8005/health | jq . || echo "ML Analytics Service: DOWN"

install: ## Install Python dependencies locally
	pip install -r requirements.txt

dev-api: ## Run API Gateway locally
	cd services/api-gateway && python main.py

dev-energy: ## Run Energy Service locally
	cd services/energy-service && python main.py

dev-water: ## Run Water Service locally
	cd services/water-service && python main.py

dev-transport: ## Run Transport Service locally
	cd services/transport-service && python main.py

dev-air: ## Run Air Quality Service locally
	cd services/air-quality-service && python main.py

dev-ml: ## Run ML Analytics Service locally
	cd services/ml-analytics-service && python main.py
