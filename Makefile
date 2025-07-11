SHELL := /bin/bash

# =============================================================================
# Configuration and Environment Variables
# =============================================================================

.DEFAULT_GOAL := help
.ONESHELL:
.EXPORT_ALL_VARIABLES:
MAKEFLAGS += --no-print-directory

# ----------------------------------------------------------------------------
# Display Formatting and Colors
# ----------------------------------------------------------------------------
BLUE := $(shell printf "\033[1;34m")
GREEN := $(shell printf "\033[1;32m")
RED := $(shell printf "\033[1;31m")
YELLOW := $(shell printf "\033[1;33m")
NC := $(shell printf "\033[0m")
INFO := $(shell printf "$(BLUE)ℹ$(NC)")
OK := $(shell printf "$(GREEN)✓$(NC)")
WARN := $(shell printf "$(YELLOW)⚠$(NC)")
ERROR := $(shell printf "$(RED)✖$(NC)")

# =============================================================================
# Help and Documentation
# =============================================================================
.PHONY: help
help: ## Display this help text for Makefile
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $1, $2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($0, 5) }' $(MAKEFILE_LIST)

.PHONY: config
config: install-uv venv ## Interactively configure the project environment.
	@echo "${INFO} Starting interactive configuration..."
	@if [ -f "$$HOME/.cargo/bin/uv" ]; then 
		export PATH="$$HOME/.cargo/bin:$$PATH"; 
	elif [ -f "$$HOME/.local/bin/uv" ]; then 
		export PATH="$$HOME/.local/bin:$$PATH"; 
	fi
	@uv run python tools/configure.py
	@echo "${OK} Configuration script finished." 

# =============================================================================
# Main Targets
# =============================================================================

.PHONY: install
install: install-uv venv db-init load-data ## Install the project, set up the database, and load all data.
	@echo "${OK} Project installation complete! 🎉"
	@echo "${INFO} You can now run the application with: make run"

.PHONY: load-data
load-data: ## Load all sample data, fixtures, and generate vector embeddings.
	@echo "${INFO} Loading database fixtures..."
	@uv run app load-fixtures
	@echo "${INFO} Generating and loading vector embeddings for products..."
	@uv run app load-vectors
	@echo "${OK} Data loading complete!"

.PHONY: run
run: ## Run the application server with hot-reloading.
	@echo "${INFO} Starting the application server..."
	@uv run app run

.PHONY: clean-db
clean-db: ## Drop the database user and all associated objects.
	@echo "${INFO} Cleaning the database..."
	@uv run python tools/clean_db.py
	@echo "${OK} Database cleaning script finished."

.PHONY: test
test: ## Run the tests
	@echo "${INFO} Running test cases... 🧪"
	@uv run pytest -n 2 --dist=loadgroup tests
	@echo "${OK} Tests complete ✨"


# =============================================================================
# Helper Targets (not intended for direct use)
# =============================================================================

.PHONY: install-uv
install-uv: # Install uv and configure PATH automatically
	@echo "${INFO} Installing uv..."
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "${INFO} Detecting installation path and updating ~/.bashrc..."
	@UV_DIR=""
	@if [ -f "$$HOME/.cargo/bin/uv" ]; then \
		UV_DIR="$$HOME/.cargo/bin"; \
	elif [ -f "$$HOME/.local/bin/uv" ]; then \
		UV_DIR="$$HOME/.local/bin"; \
	fi
	@if [ -n "$$UV_DIR" ]; then \
		if ! grep -q "$$UV_DIR" "$$HOME/.bashrc"; then \
			echo '' >> "$$HOME/.bashrc"; \
			echo '# Add Astral uv to the PATH' >> "$$HOME/.bashrc"; \
			echo "export PATH=\"$$UV_DIR:\$$PATH\"" >> "$$HOME/.bashrc"; \
			echo "${OK} Added '$UV_DIR' to your ~/.bashrc.";             echo "${INFO} Please run 'source ~/.bashrc' or restart your shell to apply the changes permanently.";         else             echo "${WARN} '$UV_DIR' is already in your ~/.bashrc.";         fi;     else         echo "${ERROR} Could not automatically find the uv installation directory. Please add it to your PATH manually.";     fi
	@echo "${OK} UV installation complete."

.PHONY: venv
venv: # Create virtual environment and install dependencies
	@echo "${INFO} Creating virtual environment and installing dependencies..."
	@if [ -f "$$HOME/.cargo/bin/uv" ]; then \
		export PATH="$$HOME/.cargo/bin:$$PATH"; \
	elif [ -f "$$HOME/.local/bin/uv" ]; then \
		export PATH="$$HOME/.local/bin:$$PATH"; \
	fi
	@uv python pin 3.12 >/dev/null 2>&1
	@uv venv >/dev/null 2>&1
	@uv sync --all-extras --dev
	@echo "${OK} Virtual environment and dependencies are set up."

.PHONY: db-init
db-init: # Initialize the database schema using the standalone script
	@echo "${INFO} Initializing the database schema via Python script..."
	@uv run python tools/init_db.py
	@echo "${OK} Database initialization script finished."

.PHONY: destroy
destroy: ## Nuke the entire project environment (venv, etc.)
	@echo "${INFO} Destroying virtual environment... 🗑️"
	@uv run pre-commit clean >/dev/null 2>&1 || true
	@rm -rf .venv
	@rm -rf node_modules
	@echo "${OK} Virtual environment destroyed 🗑️"

.PHONY: upgrade
upgrade: ## Upgrade all dependencies to latest stable versions
	@echo "${INFO} Updating all dependencies... 🔄"
	@uv lock --upgrade
	@echo "${OK} Dependencies updated 🔄"
	@uv run pre-commit autoupdate
	@echo "${OK} Updated Pre-commit hooks 🔄"

.PHONY: lock
lock: # Rebuild lockfiles from scratch
	@echo "${INFO} Rebuilding lockfiles... 🔄"
	@uv lock --upgrade >/dev/null 2>&1
	@echo "${OK} Lockfiles updated"

.PHONY: build
build: # Build the package
	@echo "${INFO} Building package... 📦"
	@uv build >/dev/null 2>&1
	@echo "${OK} Package build complete"

.PHONY: clean
clean: # Cleanup temporary build artifacts
	@echo "${INFO} Cleaning working directory... 🧹"
	@rm -rf .pytest_cache .ruff_cache .hypothesis build/ -rf dist/ .eggs/ .coverage coverage.xml coverage.json htmlcov/ .pytest_cache tests/.pytest_cache tests/**/.pytest_cache .mypy_cache .unasyncd_cache/ .auto_pytabs_cache >/dev/null 2-1
	@find . -name '*.egg-info' -exec rm -rf {} + >/dev/null 2>&1
	@find . -type f -name '*.egg' -exec rm -f {} + >/dev/null 2>&1
	@find . -name '*.pyc' -exec rm -f {} + >/dev/null 2>&1
	@find . -name '*.pyo' -exec rm -f {} + >/dev/null 2>&1
	@find . -name '*~' -exec rm -f {} + >/dev/null 2>&1
	@find . -name '__pycache__' -exec rm -rf {} + >/dev/null 2>&1
	@find . -name '.ipynb_checkpoints' -exec rm -rf {} + >/dev/null 2>&1
	@echo "${OK} Working directory cleaned"

.PHONY: coverage
coverage: # Run tests with coverage report
	@echo "${INFO} Running tests with coverage... 📊"
	@uv run pytest --cov -n 2 --dist=loadgroup --quiet
	@uv run coverage html >/dev/null 2>&1
	@uv run coverage xml >/dev/null 2>&1
	@echo "${OK} Coverage report generated ✨"

.PHONY: lint
lint: ## Run all linting checks
	@echo "${INFO} Running pre-commit checks... 🔎"
	@uv run pre-commit run --color=always --all-files
	@echo "${OK} Pre-commit checks passed ✨"

.PHONY: format
format: ## Run code formatters
	@echo "${INFO} Running code formatters... 🔧"
	@uv run ruff check --fix --unsafe-fixes
	@echo "${OK} Code formatting complete ✨"
