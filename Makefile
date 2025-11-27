.PHONY: help install test lint format clean build docs

help:
	@echo "LogInterceptor - Makefile команды"
	@echo ""
	@echo "Доступные команды:"
	@echo "  make install       - Установить зависимости для разработки"
	@echo "  make test          - Запустить все тесты"
	@echo "  make test-cov      - Запустить тесты с покрытием"
	@echo "  make lint          - Проверить код линтерами"
	@echo "  make format        - Отформатировать код"
	@echo "  make typecheck     - Проверить типы с pyright"
	@echo "  make clean         - Очистить временные файлы"
	@echo "  make build         - Собрать пакет"
	@echo "  make pre-commit    - Установить pre-commit hooks"
	@echo "  make ci            - Запустить все проверки (как в CI)"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=log_interceptor --cov-report=html --cov-report=term

test-quick:
	pytest tests/ -v -m "not slow"

lint:
	ruff check .

format:
	ruff format .

typecheck:
	pyright

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

pre-commit:
	pip install pre-commit
	pre-commit install

ci: lint typecheck test

all: format lint typecheck test

.DEFAULT_GOAL := help

