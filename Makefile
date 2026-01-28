# 🛡️ SECURE AI STUDIO - Infrastructure as Code (IaC)
# Complete automated deployment with Makefile

.PHONY: help setup build up down logs test clean status validate

# Default target
help:
	@echo "🛡️  SECURE AI STUDIO - IaC Deployment"
	@echo ""
	@echo "Available commands:"
	@echo "  setup     - Initial environment setup"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  logs      - View service logs"
	@echo "  test      - Run system validation tests"
	@echo "  clean     - Clean up environment"
	@echo "  status    - Show system status"
	@echo "  validate  - Validate deployment"
	@echo ""
	@echo "Examples:"
	@echo "  make setup"
	@echo "  make up"
	@echo "  make logs"
	@echo "  make down"

# Variables
COMPOSE_FILE := docker-compose.yml
ENV_FILE := .env
MODELS_DIR := ./models
OUTPUT_DIR := ./output
LOGS_DIR := ./logs

# Setup environment
setup: check-dependencies create-directories env-file
	@echo "✅ Environment setup complete"

check-dependencies:
	@echo "🔍 Checking dependencies..."
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "❌ Docker not found. Please install Docker"; \
		exit 1; \
	fi
	@if ! command -v docker-compose >/dev/null 2>&1; then \
		echo "❌ docker-compose not found. Please install docker-compose"; \
		exit 1; \
	fi
	@echo "✅ Docker dependencies verified"

create-directories:
	@echo "📁 Creating required directories..."
	@mkdir -p $(MODELS_DIR)/{image,video,text}
	@mkdir -p $(OUTPUT_DIR)
	@mkdir -p $(LOGS_DIR)
	@mkdir -p ./backup
	@mkdir -p ./metrics
	@chmod 700 $(MODELS_DIR) $(LOGS_DIR) ./backup
	@echo "✅ Directories created"

env-file:
	@echo "⚙️  Creating environment file..."
	@if [ ! -f "$(ENV_FILE)" ]; then \
		cp .env.example $(ENV_FILE) 2>/dev/null || echo "Creating default .env file"; \
		echo "AIR_GAP_MODE=true" > $(ENV_FILE); \
		echo "MAX_CONCURRENT_JOBS=4" >> $(ENV_FILE); \
		echo "MEMORY_LIMIT=8G" >> $(ENV_FILE); \
		echo "API_KEY=$(shell openssl rand -hex 32)" >> $(ENV_FILE); \
		echo "JWT_SECRET=$(shell openssl rand -hex 32)" >> $(ENV_FILE); \
	fi
	@echo "✅ Environment file ready"

# Build services
build:
	@echo "🏗️  Building Docker images..."
	@docker-compose -f $(COMPOSE_FILE) build --no-cache
	@echo "✅ Images built successfully"

# Start services
up: setup
	@echo "🚀 Starting Secure AI Studio..."
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Services started"
	@make status

# Stop services
down:
	@echo "🛑 Stopping Secure AI Studio..."
	@docker-compose -f $(COMPOSE_FILE) down
	@echo "✅ Services stopped"

# View logs
logs:
	@echo "📋 Service logs:"
	@docker-compose -f $(COMPOSE_FILE) logs -f

logs-engine:
	@echo "📋 AI Engine logs:"
	@docker-compose -f $(COMPOSE_FILE) logs -f secure-ai-engine

logs-monitoring:
	@echo "📋 Monitoring logs:"
	@docker-compose -f $(COMPOSE_FILE) logs -f monitoring-agent

# Run tests
test: test-unit test-integration test-security

test-unit:
	@echo "🔬 Running unit tests..."
	@docker-compose -f $(COMPOSE_FILE) run --rm secure-ai-engine \
		python -m pytest tests/ -v

test-integration:
	@echo "🔗 Running integration tests..."
	@docker-compose -f $(COMPOSE_FILE) run --rm secure-ai-engine \
		python tests/simple_offline_test.py

test-security:
	@echo "🛡️  Running security tests..."
	@docker-compose -f $(COMPOSE_FILE) run --rm secure-ai-engine \
		python tests/visual_regression_tests.py

test-load:
	@echo "🏋️  Running load tests..."
	@if command -v k6 >/dev/null 2>&1; then \
		k6 run tests/load_test_basic.js; \
	else \
		echo "⚠️  k6 not found. Install from https://k6.io/"; \
		echo "Running simulation instead..."; \
		docker-compose -f $(COMPOSE_FILE) run --rm secure-ai-engine \
			python tests/load_testing_framework.py; \
	fi

# System validation
validate: validate-containers validate-ports validate-permissions

validate-containers:
	@echo "🔍 Validating container status..."
	@docker-compose -f $(COMPOSE_FILE) ps

validate-ports:
	@echo "🔌 Validating port availability..."
	@if nc -z localhost 8000 2>/dev/null; then \
		echo "✅ API port 8000 is available"; \
	else \
		echo "⚠️  API port 8000 may not be accessible"; \
	fi

validate-permissions:
	@echo "🔐 Validating directory permissions..."
	@test -r $(MODELS_DIR) && echo "✅ Models directory readable" || echo "❌ Models directory not readable"
	@test -w $(OUTPUT_DIR) && echo "✅ Output directory writable" || echo "❌ Output directory not writable"

# Clean up
clean: down
	@echo "🧹 Cleaning up environment..."
	@docker-compose -f $(COMPOSE_FILE) rm -f
	@docker image prune -f
	@echo "✅ Cleanup complete"

clean-all: clean
	@echo "🧨 Deep cleaning (removes all data)..."
	@read -p "This will remove ALL data including models and outputs. Continue? (y/N) " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf $(MODELS_DIR)/* $(OUTPUT_DIR)/* $(LOGS_DIR)/* ./backup/* ./metrics/*; \
		echo "✅ All data removed"; \
	else \
		echo "❌ Cancelled"; \
	fi

# System status
status:
	@echo "📊 System Status"
	@echo "==============="
	@docker-compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "💾 Storage Usage:"
	@du -sh $(MODELS_DIR) $(OUTPUT_DIR) $(LOGS_DIR) ./backup ./metrics 2>/dev/null || echo "Calculating..."
	@echo ""
	@echo "🔧 System Resources:"
	@echo "CPU: $$(grep 'cpu ' /proc/stat | awk '{usage=($$2+$$4)*100/($$2+$$4+$$5)} END {print usage "%"}')"
	@echo "Memory: $$(free -h | grep Mem | awk '{print $$3 "/" $$2}')"
	
# Quick deployment (one command)
deploy: setup build up validate
	@echo "🎉 Secure AI Studio deployed successfully!"
	@echo "Access the API at: http://localhost:8000"
	@echo "View dashboard: make logs"

# Development helpers
dev-shell:
	@docker-compose -f $(COMPOSE_FILE) exec secure-ai-engine bash

dev-api-docs:
	@echo "📖 API Documentation available at: http://localhost:8000/docs"

benchmark:
	@echo "⚡ Running performance benchmark..."
	@docker-compose -f $(COMPOSE_FILE) run --rm secure-ai-engine \
		python reports/performance_reporting.py

# Backup and restore
backup:
	@echo "💾 Creating backup..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf backup/secure_ai_backup_$$timestamp.tar.gz \
		--exclude="$(MODELS_DIR)/*" \
		--exclude="./backup/*" \
		.; \
	echo "✅ Backup created: backup/secure_ai_backup_$$timestamp.tar.gz"

restore:
	@echo "🔄 Restoring from backup..."
	@read -p "Enter backup filename: " backup_file; \
	if [ -f "backup/$$backup_file" ]; then \
		tar -xzf "backup/$$backup_file" -C .; \
		echo "✅ Restore complete"; \
	else \
		echo "❌ Backup file not found"; \
	fi

# Update system
update: down pull-images build up
	@echo "⬆️  System updated successfully"

pull-images:
	@echo "⬇️  Pulling latest images..."
	@docker-compose -f $(COMPOSE_FILE) pull

# Health check
health:
	@echo "❤️  System Health Check"
	@echo "======================"
	@if curl -f http://localhost:8000/health 2>/dev/null; then \
		echo "✅ API is responding"; \
	else \
		echo "❌ API is not responding"; \
	fi
	@docker-compose -f $(COMPOSE_FILE) exec secure-ai-engine python -c "import torch; print('PyTorch OK')" 2>/dev/null && echo "✅ PyTorch working" || echo "❌ PyTorch error"
	@docker-compose -f $(COMPOSE_FILE) exec monitoring-agent python -c "import psutil; print('Monitoring OK')" 2>/dev/null && echo "✅ Monitoring working" || echo "❌ Monitoring error"

# === EVIDENCE OF QUALITY ===
evidence-report:
	@echo "📊 Generating Evidence of Quality Report..."
	python reports/evidence_of_quality_reporter.py
	@echo "✅ Evidence of Quality Report Generated"

# === SECURITY SANITIZATION ===
wipe:
	@echo "💣 EXECUTING SECURITY WIPE..."
	python security/secure_data_sanitizer.py
	@echo "✅ Security Sanitization Complete"

emergency-wipe:
	@echo "🚨 EMERGENCY SYSTEM WIPE..."
	@echo "WARNING: This will permanently destroy ALL sensitive data!"
	@read -p "Type 'CONFIRM' to proceed: " confirm && [ "$$confirm" = "CONFIRM" ]
	python -c "from security.secure_data_sanitizer import SecureDataSanitizer; SecureDataSanitizer().emergency_wipe()"
	@echo "✅ Emergency Wipe Complete"

# === CHAOS ENGINEERING ===
chaos-test:
	@echo "⚡ Running Chaos Engineering Tests..."
	python tests/chaos_engineering_simulator.py
	@echo "✅ Chaos Engineering Tests Complete"

chaos-video-test:
	@echo "🎬 Testing Video Generation Resilience..."
	python -c "from tests.chaos_engineering_simulator import ChaosEngineeringSimulator, demo_video_generation; ChaosEngineeringSimulator().run_resilience_test('video_generation_interrupt', demo_video_generation)"
	@echo "✅ Video Resilience Test Complete"

# === SPRINT TESTING ===
sprint1-test:
	@echo "🧪 Running Sprint 1: Infrastructure Stability Tests..."
	bash tests/sprint1_infra_stability.sh

sprint1-validate:
	@echo "🔬 Running Sprint 1: Comprehensive Environment Validation..."
	python tests/sprint1_comprehensive_validator.py

sprint2-test:
	@echo "⚡ Running Sprint 2: Performance and Observability Tests..."
	@echo "Coming soon: Real performance data generation"

sprint3-test:
	@echo "🌪️ Running Sprint 3: Resilience and Self-Healing Tests..."
	@echo "Coming soon: Chaos engineering validation"

sprint4-test:
	@echo "🛡️ Running Sprint 4: Security and Audit Tests..."
	@echo "Coming soon: Content security validation"