# PCARA Development Makefile

.PHONY: help start stop test logs clean build

# Default target
help:
	@echo "🚀 PCARA Development Commands"
	@echo "==============================="
	@echo "start    - Start development environment"
	@echo "stop     - Stop all services"
	@echo "test     - Run setup tests"
	@echo "logs     - Show all service logs"
	@echo "clean    - Stop and remove all containers/volumes"
	@echo "build    - Build all services"
	@echo "db-shell - Connect to PostgreSQL database"
	@echo "api-logs - Show API Gateway logs"
	@echo "help     - Show this help message"

# Start development environment
start:
	@echo "🚀 Starting PCARA development environment..."
	@docker-compose -f docker-compose.dev.yml up -d --build
	@echo "✅ Services started. Access frontend at http://localhost:3001"

# Stop all services
stop:
	@echo "🛑 Stopping PCARA services..."
	@docker-compose -f docker-compose.dev.yml down

# Run tests
test:
	@echo "🧪 Running PCARA setup tests..."
	@sleep 5  # Wait for services to be ready
	@python3 test-setup.py

# Show logs for all services
logs:
	@docker-compose -f docker-compose.dev.yml logs -f

# Show API Gateway logs specifically
api-logs:
	@docker-compose -f docker-compose.dev.yml logs -f api-gateway

# Clean everything (remove containers and volumes)
clean:
	@echo "🧹 Cleaning up PCARA environment..."
	@docker-compose -f docker-compose.dev.yml down -v
	@docker system prune -f

# Build all services
build:
	@echo "🔨 Building PCARA services..."
	@docker-compose -f docker-compose.dev.yml build

# Connect to database shell
db-shell:
	@docker-compose -f docker-compose.dev.yml exec postgres psql -U pcara_user -d pcara_dev

# Check service status
status:
	@echo "📊 PCARA Service Status:"
	@echo "========================"
	@docker-compose -f docker-compose.dev.yml ps