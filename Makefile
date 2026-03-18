# Makefile for common tasks

.PHONY: help install dev-install db-init db-drop run test lint format clean docker-up docker-down

help:
	@echo "Ghost Investor AI - Development Tasks"
	@echo "======================================"
	@echo ""
	@echo "Available targets:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev-install   - Install dependencies + dev tools"
	@echo "  make db-init       - Initialize database"
	@echo "  make db-drop       - Drop all database tables"
	@echo "  make run           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make examples      - Run example workflows"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

db-init:
	python cli.py db-init

db-drop:
	python cli.py db-drop

run:
	python cli.py run

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

examples:
	python examples.py

.DEFAULT_GOAL := help
