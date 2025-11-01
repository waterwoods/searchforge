.PHONY: help install up-qdrant start wait smoke e2e baselines sweep-rrf sweep-rerank sweep-conc verify full full-auto fiqa-fast

SHELL := /bin/bash

## ===== Ports & Base =====

MAIN_PORT ?= 8011

BASE ?= http://localhost:$(MAIN_PORT)

CONC ?= 8

## ===== Utilities =====

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { echo "❌ Missing dependency: $(1). Please install it."; exit 1; }
endef

help:
	@echo "Targets:"
	@echo "  make full         - Run smoke + e2e + sweeps + verify (backend must be running)"
	@echo "  make full-auto    - Auto-start backend (if needed), wait health, then run full"
	@echo "  make install      - Poetry install"
	@echo "  make up-qdrant    - Start Qdrant via docker compose"
	@echo "  make start        - Start backend on MAIN_PORT ($(MAIN_PORT))"
	@echo "  make wait         - Wait for health on $(BASE)"
	@echo "  make smoke        - Run 3-step smoke tests"
	@echo "  make e2e          - Run end-to-end self tests"
	@echo "  make baselines    - Run FiQA baseline group"
	@echo "  make sweep-rrf    - Sweep RRF k values"
	@echo "  make sweep-rerank - Sweep reranker margin/budget"
	@echo "  make sweep-conc   - Sweep concurrency levels"
	@echo "  make verify       - Show key fields from reports/_latest/best.yaml"
	@echo "  make fiqa-fast    - Quick trend run: baseline+rrf+gated with --fast flag (200 samples, 1 repeat, concurrency 16)"

install:
	$(call ensure_tool,poetry)
	poetry install
	@echo "✅ poetry install done"

up-qdrant:
	@command -v docker >/dev/null 2>&1 || { echo '❌ docker not found'; exit 1; }
	@{ command -v docker-compose >/dev/null 2>&1 && docker-compose up -d qdrant; } || { docker compose up -d qdrant; }
	@echo "⛳ Qdrant started (detached)"

start:
	$(call ensure_tool,poetry)
	@echo "▶ Starting backend on MAIN_PORT=$(MAIN_PORT)"
	@MAIN_PORT=$(MAIN_PORT) nohup poetry run bash services/fiqa_api/start_server.sh >/tmp/fiqa_api.log 2>&1 &
	@echo "  logs: /tmp/fiqa_api.log"

wait:
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	@echo "⏳ Waiting for health at $(BASE) ..."
	@BASE="$(BASE)" bash -lc 'set -e; for i in {1..30}; do \
	  if curl -s --connect-timeout 0.5 --max-time 1.5 "$$BASE/api/health/qdrant" | jq -e ".http_ok and .grpc_ok" >/dev/null; then \
	    echo "✅ Health OK on $$BASE"; exit 0; fi; \
	  sleep 0.5; done; echo "❌ Backend not ready on $$BASE" >&2; exit 1'

smoke:
	$(call ensure_tool,bash)
	$(call ensure_tool,bc)
	$(call ensure_tool,jq)
	@echo "🔥 Smoke tests @ $(BASE)"
	@BASE="$(BASE)" bash scripts/smoke.sh
	@echo "✅ SMOKE OK"

e2e:
	$(call ensure_tool,bash)
	$(call ensure_tool,jq)
	@echo "🔁 End-to-End tests @ $(BASE)"
	@BASE="$(BASE)" bash scripts/self_test.sh
	@echo "🎉 E2E OK"

baselines:
	$(call ensure_tool,poetry)
	@echo "📊 Baseline group @ $(BASE), conc=$(CONC)"
	@poetry run python experiments/fiqa_suite_runner.py \
	  --groups baseline --concurrency $(CONC) --base $(BASE)
	@echo "✅ Baseline OK"

sweep-rrf:
	$(call ensure_tool,poetry)
	@echo "🔎 RRF sweep (k in 10 30 60) @ $(BASE), conc=$(CONC)"
	@bash -lc 'set -e; for k in 10 30 60; do \
	  echo "  → rrf_k=$$k"; \
	  poetry run python experiments/fiqa_suite_runner.py \
	    --groups rrf --rrf-k $$k --concurrency $(CONC) --base $(BASE); \
	done'
	@echo "✅ RRF sweep OK"

sweep-rerank:
	$(call ensure_tool,poetry)
	@echo "🧠 Rerank sweep (margin x budget-ms) @ $(BASE), conc=$(CONC)"
	@bash -lc 'set -e; for m in 0.05 0.10; do for b in 50 120; do \
	  echo "  → margin=$$m, budget_ms=$$b"; \
	  poetry run python experiments/fiqa_suite_runner.py \
	    --groups gated --rerank-margin $$m --rerank-budget-ms $$b \
	    --concurrency $(CONC) --base $(BASE); \
	done; done'
	@echo "✅ Rerank sweep OK"

sweep-conc:
	$(call ensure_tool,poetry)
	@echo "⚙ Concurrency sweep (1 4 8 16) @ $(BASE)"
	@bash -lc 'set -e; for c in 1 4 8 16; do \
	  echo "  → concurrency=$$c"; \
	  poetry run python experiments/fiqa_suite_runner.py \
	    --groups baseline,rrf,gated --concurrency $$c --base $(BASE); \
	done'
	@echo "✅ Concurrency sweep OK"

verify:
	@echo "🔎 Verify best.yaml (top 120 lines)"
	@{ test -f reports/_latest/best.yaml && head -120 reports/_latest/best.yaml; } || \
	  { echo "⚠ reports/_latest/best.yaml not found"; exit 1; }
	@echo "✅ Verify OK"

full: smoke e2e baselines sweep-rrf sweep-rerank sweep-conc verify
	@echo "🎉 FULL RUN DONE (BASE=$(BASE), MAIN_PORT=$(MAIN_PORT))"

full-auto:
	@echo "▶ Auto-start backend if needed (MAIN_PORT=$(MAIN_PORT)) ..."
	@{ curl -s "$(BASE)/api/health/qdrant" | jq -e ".http_ok and .grpc_ok" >/dev/null 2>&1 || \
	  ( $(MAKE) start && $(MAKE) wait ); }
	@$(MAKE) full

fiqa-fast:
	$(call ensure_tool,poetry)
	@echo "⚡ Quick trend run: baseline+rrf+gated with --fast flag"
	@poetry run python experiments/fiqa_suite_runner.py --groups baseline rrf gated --top_k 50 --fast
	@echo "✅ FiQA fast run complete"

tune-fast:
	$(call ensure_tool,poetry)
	@echo "🔎 Random+EarlyStop (fast stage)"
	@poetry run python experiments/fiqa_tuner.py --fast \
		--n-trials $(or $(MAX_TRIALS),40) \
		--patience $(or $(PATIENCE),10) \
		--min-improve $(or $(MIN_IMPROVE),0.005) \
		--seed 42

tune-full:
	$(call ensure_tool,poetry)
	@echo "✅ Promote top-k to full evaluation"
	@poetry run python experiments/fiqa_tuner.py --promote --promote-top-k 3 --timeout 20

tune-fast-sane:
	$(call ensure_tool,poetry)
	@echo "▶ Fast tuning (sane load)"
	@MAIN_PORT?=8011 WORKERS?=4 QUERY_TIMEOUT_S?=20 \
		CLIENT_TIMEOUT_S?=30 FAST_SAMPLE?=150 FAST_TOP_K?=30 \
		FAST_CONCURRENCY?=8 poetry run python experiments/fiqa_tuner.py --fast
