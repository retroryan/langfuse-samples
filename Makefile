# Makefile for langfuse-samples

.PHONY: help setup check install-deps lint format test clean

help:  ## Show this help message
	@echo "Langfuse Samples - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## Run interactive setup for all components
	python setup.py

check:  ## Check current setup and validate environment
	python setup.py --check

install-deps:  ## Install dependencies for all components
	python setup.py --install-deps

lint:  ## Run code linting with flake8
	@echo "Running flake8 linting..."
	@python -m flake8 . || echo "Install flake8 with: pip install flake8"

format:  ## Format code with black (if available)
	@echo "Formatting code with black..."
	@python -m black . --check || echo "Install black with: pip install black"

test-ollama:  ## Run ollama integration tests
	cd ollama-langfuse && python run_and_validate.py

test-strands:  ## Run strands integration tests  
	cd strands-langfuse && python run_and_validate.py

test: test-ollama test-strands  ## Run all integration tests

clean:  ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

clean-traces:  ## Clean up Langfuse traces and scores
	python utils/delete_metrics.py --yes

# Component-specific targets
setup-ollama:  ## Setup ollama component only
	python setup.py --component ollama

setup-strands:  ## Setup strands component only
	python setup.py --component strands  

setup-aws:  ## Setup AWS deployment component only
	python setup.py --component aws