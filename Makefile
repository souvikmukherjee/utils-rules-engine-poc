.PHONY: install-py install-web api web test

install-py:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e packages/rules_engine -e apps/api pytest httpx

install-web:
	pnpm install

api:
	. .venv/bin/activate && \
	PYTHONPATH=packages/rules_engine/src:apps/api/src \
	uvicorn rules_api.main:app --reload \
		--reload-dir apps/api \
		--reload-dir packages/rules_engine \
		--host 127.0.0.1 --port 8000

web:
	pnpm dev:web

test:
	. .venv/bin/activate && \
	PYTHONPATH=packages/rules_engine/src:apps/api/src \
	pytest packages/rules_engine/tests apps/api/tests -q
