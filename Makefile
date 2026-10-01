.PHONY: dev up down build test lint clean

# ── Development ─────────────────────────────────────────────────
dev:
	docker compose up --build

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

# ── Backend ─────────────────────────────────────────────────────
backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && pytest tests/ -v

backend-lint:
	cd backend && python -m py_compile app/main.py

# ── Frontend ────────────────────────────────────────────────────
frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npx tsc --noEmit

# ── Testing ─────────────────────────────────────────────────────
test: backend-test

# ── Evaluation ──────────────────────────────────────────────────
eval:
	cd backend && python -m app.evaluation.cli

# ── Cleanup ─────────────────────────────────────────────────────
clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next
