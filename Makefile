.PHONY: help install dev-install format lint test docker-up docker-down migrate db-shell redis-shell clean

help:
	@echo "CarScout AI - Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo "  make format       - Format code with black and ruff"
	@echo "  make lint         - Run linters (ruff, mypy)"
	@echo "  make test         - Run tests with pytest"
	@echo "  make docker-up    - Start all services with docker-compose"
	@echo "  make docker-down  - Stop all services"
	@echo "  make migrate      - Run database migrations"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo "  make redis-shell  - Open Redis CLI"
	@echo "  make clean        - Clean up cache and build files"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"
	playwright install

format:
	black .
	ruff check --fix .

lint:
	ruff check .
	mypy apps/ workers/ libs/

test:
	pytest tests/ -v --cov=apps --cov=workers --cov=libs

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

db-shell:
	docker exec -it carscout-postgres psql -U carscout -d carscout_ai

redis-shell:
	docker exec -it carscout-redis redis-cli

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info
