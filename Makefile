.PHONY: install-py install-web api web test

install-py:
	python3 -m venv .venv || true
	if [ -f .venv/bin/activate ]; then \
		. .venv/bin/activate && pip install -U pip && pip install -e packages/rules_engine -e apps/api pytest httpx; \
	else \
		pip3 install -U pip && pip3 install -e packages/rules_engine -e apps/api pytest httpx; \
	fi

install-web:
	pnpm install

api:
	@if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi; \
	PYTHONPATH=packages/rules_engine/src:apps/api/src \
	uvicorn rules_api.main:app --reload \
		--reload-dir apps/api \
		--reload-dir packages/rules_engine \
		--host 127.0.0.1 --port 8000

web:
	pnpm dev:web

test:
	@if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi; \
	PYTHONPATH=packages/rules_engine/src:apps/api/src \
	pytest packages/rules_engine/tests apps/api/tests -q
