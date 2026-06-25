.PHONY: setup-api setup-web setup dev-api dev-web dev test clean

# ── Setup ─────────────────────────────────────────────────────────

setup-api:
	pip install -r apps/api/requirements.txt

setup-web:
	cd apps/web && npm install

setup: setup-api setup-web

# ── Development ────────────────────────────────────────────────────

dev-api:
	cd apps/api && python -m app.main

dev-web:
	cd apps/web && npm run dev

# Runs both API and web in parallel (Unix: &, Windows: start)
dev:
	$(MAKE) dev-api & $(MAKE) dev-web

# ── Testing ────────────────────────────────────────────────────────

test-api:
	cd apps/api && python -m pytest tests/ -v

test: test-api

# ── Cleanup ────────────────────────────────────────────────────────

clean:
	rm -rf apps/api/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/web/.next
