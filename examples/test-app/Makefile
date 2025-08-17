# Makefile for E2E Amplitude testing

# Default values
BASE_URL ?= http://localhost:8050
AMPLITUDE_API_KEY ?= da0e05f882b7795f28eaba07890d418d
OUTPUT_DIR ?= ./test_flows
ITERATIONS ?= 3

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
RESET := \033[0m

.PHONY: help install start-app stop-app generate-events extract-flows full-e2e clean

help: ## Show this help message
	@echo "TestGenesis E2E Amplitude Testing"
	@echo "================================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "Environment variables:"
	@echo "  BASE_URL           Test app URL (default: $(BASE_URL))"
	@echo "  AMPLITUDE_API_KEY  Amplitude API key (default: hidden)"
	@echo "  OUTPUT_DIR         Output directory for flows (default: $(OUTPUT_DIR))"
	@echo "  ITERATIONS         Number of test iterations (default: $(ITERATIONS))"

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(RESET)"
	pip install playwright
	playwright install chromium
	@echo "$(GREEN)✓ Dependencies installed$(RESET)"

start-app: ## Start the test application
	@echo "$(GREEN)Starting test app...$(RESET)"
	@if lsof -Pi :8050 -sTCP:LISTEN -t >/dev/null ; then \
		echo "$(RED)App already running on port 8050$(RESET)"; \
	else \
		nohup python app.py > app.log 2>&1 & \
		echo $$! > app.pid; \
		sleep 3; \
		echo "$(GREEN)✓ Test app started (PID: $$(cat app.pid))$(RESET)"; \
	fi

stop-app: ## Stop the test application
	@echo "$(GREEN)Stopping test app...$(RESET)"
	@if [ -f app.pid ]; then \
		kill $$(cat app.pid) 2>/dev/null || true; \
		rm -f app.pid; \
		echo "$(GREEN)✓ Test app stopped$(RESET)"; \
	else \
		echo "$(RED)No app.pid file found$(RESET)"; \
	fi

generate-events: ## Generate Amplitude events using Playwright
	@echo "$(GREEN)Generating Amplitude events...$(RESET)"
	@echo "Base URL: $(BASE_URL)"
	@echo "Iterations: $(ITERATIONS)"
	python e2e_amplitude_generator.py \
		--base-url $(BASE_URL) \
		--iterations $(ITERATIONS) \
		--headless \
		--include-errors
	@echo "$(GREEN)✓ Events generated$(RESET)"

extract-flows: ## Extract flows from Amplitude
	@echo "$(GREEN)Extracting flows from Amplitude...$(RESET)"
	@echo "Output directory: $(OUTPUT_DIR)"
	@mkdir -p $(OUTPUT_DIR)
	testgenesis amplitude extract-flows \
		--api-key $(AMPLITUDE_API_KEY) \
		--start-date $$(date -v-1d +%Y-%m-%d) \
		--end-date $$(date +%Y-%m-%d) \
		--output-dir $(OUTPUT_DIR)
	@echo "$(GREEN)✓ Flows extracted to $(OUTPUT_DIR)$(RESET)"

full-e2e: ## Run complete E2E flow (generate + extract)
	@echo "$(GREEN)Running complete E2E flow...$(RESET)"
	python e2e_amplitude_generator.py \
		--base-url $(BASE_URL) \
		--iterations $(ITERATIONS) \
		--headless \
		--include-errors \
		--extract \
		--api-key $(AMPLITUDE_API_KEY) \
		--output-dir $(OUTPUT_DIR)
	@echo "$(GREEN)✓ Complete E2E flow finished$(RESET)"

generate-tests: ## Generate test code from extracted flows
	@echo "$(GREEN)Generating test code...$(RESET)"
	@for flow in $(OUTPUT_DIR)/*.json; do \
		if [ -f "$$flow" ]; then \
			echo "Processing: $$flow"; \
			testgenesis generate "$$flow" \
				--framework playwright \
				--output "tests/generated/$$(basename $$flow .json).spec.ts"; \
		fi \
	done
	@echo "$(GREEN)✓ Test code generated$(RESET)"

verify: ## Verify that events are being received
	@echo "$(GREEN)Verifying Amplitude connection...$(RESET)"
	@echo "Checking for recent flows..."
	@if [ -d "$(OUTPUT_DIR)" ] && [ "$$(ls -A $(OUTPUT_DIR) 2>/dev/null)" ]; then \
		echo "$(GREEN)✓ Found flows in $(OUTPUT_DIR):$(RESET)"; \
		ls -la $(OUTPUT_DIR)/*.json | head -5; \
	else \
		echo "$(RED)✗ No flows found. Run 'make extract-flows' first$(RESET)"; \
	fi

clean: ## Clean up generated files and logs
	@echo "$(GREEN)Cleaning up...$(RESET)"
	rm -rf $(OUTPUT_DIR)
	rm -f generated_events.json
	rm -f app.log app.pid
	rm -rf tests/generated
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

.DEFAULT_GOAL := help