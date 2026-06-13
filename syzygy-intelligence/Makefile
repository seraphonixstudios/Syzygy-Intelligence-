.PHONY: lint lint-fix test test-all e2e dev dev-backend dev-frontend dev-mock ollama ollama-docker clean

BACKEND = backend
FRONTEND = frontend

lint:
	cd $(BACKEND) && python -m ruff check .

lint-fix:
	cd $(BACKEND) && python -m ruff check --fix .

test:
	cd $(BACKEND) && python -m pytest tests/ -q --tb=short

test-all:
	cd $(BACKEND) && OLLAMA_BASE_URL=http://localhost:11435 python -m pytest tests/ -q --tb=short

e2e:
	cd $(FRONTEND) && set NEXT_PUBLIC_SYZYGY_API_URL=http://localhost:8000 && npx playwright test

ollama:
	@echo "Run: .\scripts\setup-ollama.ps1  (Windows)"
	@echo "Or:  ollama pull qwen2.5:7b && ollama cp qwen2.5:7b qwen3:8b-gpu"
	@echo "     ollama pull dolphin-llama3:8b && ollama cp dolphin-llama3:8b dolphin-llama3:8b-gpu"

ollama-docker:
	docker compose -f docker-compose.yml -f docker-compose.ollama-cpu.yml up -d ollama

dev-mock:
	cd $(BACKEND) && python -m uvicorn tests.mock_ollama_server:app --host 0.0.0.0 --port 11435

dev-backend:
	cd $(BACKEND) && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

dev-frontend:
	cd $(FRONTEND) && npx next dev

dev: dev-mock dev-backend dev-frontend

clean:
	cd $(BACKEND) && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; rm -rf .pytest_cache data/syzygy.db data/chroma
	cd $(FRONTEND) && rm -rf .next/cache test-results playwright-report

all: lint test