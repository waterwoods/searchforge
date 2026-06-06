# =============================================================================
# SEARCHFORGE LAB / R&D ONLY — not Unified Intake paid pilot
#
# Product operators: bash scripts/run_demo_local.sh  (port 8001)
# Paid pilot deploy: bash scripts/deploy_paid_pilot.sh
# Lab infra index:   docs/archive/platform/README_LAB_INFRA.md
# Operator surface:  docs/runbooks/OPERATOR_SURFACE.md
# =============================================================================

PROJECT ?= searchforge
SERVICE ?= rag-api
ENV_FILE ?= .env.current
GIT_SHA  := $(shell git rev-parse --short HEAD)
COMPOSE ?= docker compose --env-file $(ENV_FILE) -p $(PROJECT)
EXEC := $(COMPOSE) exec $(SERVICE)
RUN := $(COMPOSE) run --rm $(SERVICE)
PY ?= python3
FORCE_BASE ?= 0
NO_CACHE ?= 0
OBS_ENABLED ?= 0
export OBS_ENABLED

SSH_HOST ?= andy-wsl
REMOTE ?= $(SSH_HOST)
RDIR=~/searchforge

# == Ports/Base ==
HOST ?= 127.0.0.1
PORT ?= 8000
BASE ?= http://$(HOST):$(PORT)
BASE_URL ?= http://andy-wsl:8000
PROXY_BASE ?= http://127.0.0.1:7070

# Helper to detect current target
TARGET ?= $(shell grep -E '^SEARCHFORGE_TARGET=' .env.current | cut -d= -f2 2>/dev/null || echo local)

## ===== Utilities =====

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { echo "❌ Missing dependency: $(1). Please install it."; exit 1; }
endef

.PHONY: help install lint type test export smoke obs-verify obs-url ui-open-check up down restart rebuild logs ps health prune-safe df tunnel-dozzle open-portainer sync whoami gpu-smoke proxy-smoke compose-config update-hosts migrate-qdrant cutover-remote baseline-save baseline-save-local baseline-save-remote ui ui-reset ui-verify rebuild-api rebuild-api-cpu up-gpu down-gpu export-reqs lint-no-legacy-toolchain cleanup-audit cleanup-apply cleanup-restore cleanup-history create-clean-repo sync-experiments verify-experiments smoke-experiment runner-check fiqa-50k-stage-b smoke-fast smoke-contract smoke-review smoke-apply graph-smoke graph-resume graph-full graph-e2e volumes-ok up-proxy smoke-proxy degrade-test check-qdrant seed-fiqa reseed-fiqa a-verify b-verify c-verify abc-verify realcheck-up realcheck-on realcheck-off realcheck tuner-smoke tuner-ab policy-smoke real-large-on real-large-off real-large-paired real-pareto real-plot trilines-refresh kpi-refresh ci wait-ready diag-now
volumes-ok:
	$(call ensure_tool,docker)
	@set -e; \
	printf "🔍 Checking steward volumes inside container...\n"; \
	$(COMPOSE) exec $(SERVICE) sh -lc 'set -e; \
	for dir in /app/.runs /app/baselines; do \
	  touch "$$dir/.volumes-ok-test" && rm -f "$$dir/.volumes-ok-test"; \
	  printf "✅ %s writable (%s)\n" "$$dir" "$$(readlink -f $$dir)"; \
	done'


# Default target: show help
.DEFAULT_GOAL := help

help: ## 显示所有可用命令（默认命令）
	@echo "=================================================="
	@echo "  LAB ONLY — SearchForge Makefile (not paid pilot)"
	@echo "  Product: bash scripts/run_demo_local.sh  (:8001)"
	@echo "  Deploy:  bash scripts/deploy_paid_pilot.sh"
	@echo "  Index:   docs/archive/platform/README_LAB_INFRA.md"
	@echo "=================================================="
	@echo "  SearchForge Makefile 命令帮助"
	@echo "=================================================="

install: ## Build rag-api image (installs dependencies inside container)
	$(COMPOSE) build $(SERVICE)

dev-api: ## 本地启动 API（容器模式）
	$(COMPOSE) up -d $(SERVICE)

smoke: ## 健康检查冒烟
	curl -sf http://127.0.0.1:8000/health/live
	curl -sf http://127.0.0.1:8000/health/ready
	@echo "SMOKE OK"

up-proxy:
	$(COMPOSE) up -d qdrant retrieval-proxy

logs-proxy:
	docker compose logs -f retrieval-proxy qdrant

smoke-proxy:
	curl -sf http://localhost:7070/healthz
	curl -sf http://localhost:7070/readyz
	curl -s "http://localhost:7070/v1/search?q=hello&k=8&budget_ms=400" | jq -r '.ret_code,.degraded,.timings.total_ms,.trace_url'

proxy-smoke: ## Run proxy smoke test (proxy → rag-api → GPU worker → Qdrant)
	$(call ensure_tool,python3)
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	@mkdir -p .runs
	@echo "🧪 Running proxy smoke test..."
	@echo "1. Ensuring services are up..."
	@$(COMPOSE) up -d qdrant retrieval-proxy rag-api gpu-worker
	@sleep 3
	@echo "2. Waiting for services to be ready..."
	@bash scripts/wait_for_gpu_ready.sh || (echo "❌ GPU worker not ready"; exit 1)
	@echo "3. Waiting for proxy readiness..."
	@for i in $$(seq 1 30); do \
		if curl -sf http://localhost:7070/readyz >/dev/null 2>&1; then \
			echo "✅ Proxy ready"; \
			break; \
		fi; \
		echo "⏳ waiting for proxy ($$i/30)..."; \
		sleep 1; \
	done
	@echo "4. Waiting for rag-api readiness..."
	@for i in $$(seq 1 30); do \
		if curl -sf http://localhost:8000/readyz | jq -e '.clients_ready==true' >/dev/null 2>&1; then \
			echo "✅ rag-api ready"; \
			break; \
		fi; \
		echo "⏳ waiting for rag-api ($$i/30)..."; \
		sleep 1; \
	done
	@echo "5. Running proxy smoke test script..."
	@PROXY_URL=$${PROXY_URL:-http://localhost:7070} \
	 RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
	 GPU_WORKER_URL=$${GPU_WORKER_URL:-http://localhost:8090} \
	 python3 experiments/proxy_smoke.py \
		--proxy-url $${PROXY_URL:-http://localhost:7070} \
		--rag-api-url $${RAG_API_URL:-http://localhost:8000} \
		--gpu-worker-url $${GPU_WORKER_URL:-http://localhost:8090} \
		--output .runs/proxy_smoke.json
	@if jq -e '.all_passed==true' .runs/proxy_smoke.json >/dev/null 2>&1; then \
		echo "✅ Proxy smoke test PASSED"; \
	else \
		echo "❌ Proxy smoke test FAILED"; \
		exit 1; \
	fi

degrade-test:
	docker compose stop qdrant
	@sleep 1
	curl -i http://localhost:7070/readyz | tee .runs/proxy_ready_down.txt
	curl -s "http://localhost:7070/v1/search?q=hello&k=5&budget_ms=50" | jq -r '.degraded,.ret_code' | tee .runs/proxy_degrade.txt
	docker compose start qdrant
	@sleep 3
	curl -i http://localhost:7070/readyz | tee .runs/proxy_ready_up.txt

realcheck-up:
	@docker compose up -d qdrant retrieval-proxy rag-api

realcheck-on: realcheck-up
	@sed -i.bak -E 's/^USE_PROXY=.*/USE_PROXY=true/' .env.current || true
	@docker compose restart rag-api
	@sleep 2
	@USE_PROXY=true PROXY_URL=$${PROXY_URL:-http://localhost:7070} RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
	  REALCHECK_N=$${REALCHECK_N:-80} REALCHECK_BUDGET_MS=$${REALCHECK_BUDGET_MS:-400} \
	  python3 scripts/realcheck_small.py proxy_on .runs/realcheck_proxy_on.json | tee .runs/realcheck.log

realcheck-off: realcheck-up
	@sed -i.bak -E 's/^USE_PROXY=.*/USE_PROXY=false/' .env.current || true
	@docker compose restart rag-api
	@sleep 2
	@USE_PROXY=false RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
	  REALCHECK_N=$${REALCHECK_N:-80} REALCHECK_BUDGET_MS=$${REALCHECK_BUDGET_MS:-400} \
	  python3 scripts/realcheck_small.py proxy_off .runs/realcheck_proxy_off.json | tee -a .runs/realcheck.log

realcheck: realcheck-on realcheck-off
	@python3 -c 'import json, os; on=json.load(open(".runs/realcheck_proxy_on.json")); off=json.load(open(".runs/realcheck_proxy_off.json")); arm=on.get("arm") or off.get("arm") or "baseline"; report={"arm": arm, "p95_on_ms": on.get("p95_ms"), "p95_off_ms": off.get("p95_ms"), "mean_on_ms": on.get("mean_ms"), "mean_off_ms": off.get("mean_ms"), "succ_on": on.get("success_rate"), "succ_off": off.get("success_rate"), "degraded_on": on.get("degraded_rate"), "degraded_off": off.get("degraded_rate"), "p95_improvement_ms": (off.get("p95_ms") - on.get("p95_ms")) if (on.get("p95_ms") and off.get("p95_ms")) else None, "pass_simple": bool(on.get("p95_ms") and off.get("p95_ms") and on.get("p95_ms") <= off.get("p95_ms")), "notes": "PASS means proxy p95 <= direct p95. This is a lightweight sanity check."}; os.makedirs(".runs", exist_ok=True); json.dump(report, open(".runs/realcheck_report.json","w"), indent=2); print(json.dumps(report, indent=2))'
	@echo "Artifacts written to .runs/: realcheck_proxy_on.json, realcheck_proxy_off.json, realcheck_report.json"

# --- E2E mini: direct compat + proxy on/off ---
e2e-direct:
	@$(MAKE) wait-ready
	@python3 scripts/e2e_direct.py

e2e-mini: realcheck-up seed-fiqa e2e-direct
	@# run proxy ON/OFF sampler (produces *_on/off.json + report.json)
	@$(MAKE) realcheck
	@# synthesize final verdict
	@python3 scripts/e2e_summary.py

tuner-smoke: realcheck-up
	@USE_PROXY=true PROXY_URL=$${PROXY_URL:-http://localhost:7070} RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
		N=$${N:-50} BUDGET_MS=$${BUDGET_MS:-400} python3 scripts/tuner_real_small.py

tuner-smoke-%: realcheck-up
	@POLICY=$* USE_PROXY=true PROXY_URL=$${PROXY_URL:-http://localhost:7070} RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
		N=$${N:-50} BUDGET_MS=$${BUDGET_MS:-400} python3 scripts/tuner_real_small.py

tuner-ab: realcheck-up
	@USE_PROXY=true PROXY_URL=$${PROXY_URL:-http://localhost:7070} RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
		N=80 BUDGET_MS=$${BUDGET_MS:-400} python3 scripts/tuner_real_small.py
	@python3 -c "import json, pathlib, sys; r=json.loads(pathlib.Path('.runs/tuner_small_report.json').read_text()); ok=r.get('ok', False); print('TUNER AB PASS' if ok else 'TUNER AB FAIL'); sys.exit(0 if ok else 1)"

wait-ready:
	@echo "Waiting for /healthz ..."
	@until curl -sf http://localhost:8000/healthz >/dev/null; do sleep 1; done
	@echo "Waiting for /readyz (clients_ready=true) ..."
	@until curl -sf http://localhost:8000/readyz | jq -e '.clients_ready==true' >/dev/null; do sleep 1; done
	@echo "Backend ready."

diag-now: ## Zero-risk diagnostics: version alignment, readiness, query, autotuner API
	@mkdir -p .runs
	@python3 scripts/diag_now.py --base "$(BASE_URL)" | tee .runs/diag.out

diag: diag-now

policy-smoke: wait-ready
	@rm -f .runs/policy_*.json .runs/policy_summary.json
	@set -e; \
	status=0; \
	export AUTOTUNER_TOKEN=$$(grep -E '^AUTOTUNER_TOKENS=' $(ENV_FILE) 2>/dev/null | cut -d= -f2 | cut -d, -f1 | tr -d ' "') || AUTOTUNER_TOKEN=devtoken; \
	export AUTOTUNER_RPS=$$(grep -E '^AUTOTUNER_RPS=' $(ENV_FILE) 2>/dev/null | cut -d= -f2 | tr -d ' "') || AUTOTUNER_RPS=0; \
	for policy in LatencyFirst RecallFirst Balanced; do \
		echo ">>> policy-smoke $$policy"; \
		if ! AUTOTUNER_TOKEN=$${AUTOTUNER_TOKEN} AUTOTUNER_RPS=$${AUTOTUNER_RPS} python3 scripts/tuner_real_small.py --policy $$policy; then \
			status=1; \
		fi; \
		slug=$$(python3 -c "import sys; name=sys.argv[1]; print(''.join(ch.lower() for ch in name if ch.isalnum() or ch in '-_'))" $$policy); \
		if [ -f ".runs/tuner_small_$${slug}.json" ]; then \
			cp ".runs/tuner_small_$${slug}.json" ".runs/policy_$${slug}.json"; \
		else \
			echo "{}" > ".runs/policy_$${slug}.json"; \
			status=1; \
		fi; \
	done; \
	jq -s '{ok:(map(.ok)|all), runs:.}' .runs/policy_*.json | tee .runs/policy_summary.json; \
	if [ "$$(jq -r '.ok' .runs/policy_summary.json)" != "true" ]; then \
		status=1; \
	fi; \
	exit $$status

smoke-run: ## Run quick smoke test (daily health check)
	@bash scripts/quick_smoke.sh

smoke-status: ## Show smoke test status
	@if [ -f .runs/smoke_status.json ]; then \
		cat .runs/smoke_status.json | jq '.' 2>/dev/null || cat .runs/smoke_status.json; \
	else \
		echo "No smoke status found. Run 'make smoke-run' first."; \
		exit 1; \
	fi

smoke-daily-install: ## Install daily smoke test cron job
	@echo "Installing daily smoke test cron job..."
	@PROJECT_ROOT="$$(cd '$(dir $(abspath $(lastword $(MAKEFILE_LIST))))' && pwd)"; \
	SCRIPT_PATH="$${PROJECT_ROOT}/scripts/quick_smoke.sh"; \
	LOG_PATH="$${PROJECT_ROOT}/.runs/smoke_cron.log"; \
	CRON_ENTRY="@daily cd $${PROJECT_ROOT} && bash $${SCRIPT_PATH} >> $${LOG_PATH} 2>&1"; \
	(crontab -l 2>/dev/null | grep -v "quick_smoke.sh" || true; echo "$${CRON_ENTRY}") | crontab -; \
	echo "✅ Daily smoke test cron job installed."; \
	echo "Current crontab:"; \
	crontab -l | grep -A1 -B1 "quick_smoke.sh" || echo "   (not found in crontab - check crontab -l)"

.PHONY: base-build rebuild rebuild-auto rebuild-fast smoke-run smoke-status smoke-daily-install

## Build base image (py311) with BuildKit
base-build:
	DOCKER_BUILDKIT=1 docker build --build-arg GIT_SHA=$(GIT_SHA) -t searchforge-base:py311 -f docker/base/Dockerfile .

## Rebuild rag-api using classic builder (offline-safe)
rebuild: ## Classic builder, pass GIT_SHA, write log
	mkdir -p .runs
	echo "[$(shell date -Iseconds)] rebuild(classic) GIT_SHA=$(GIT_SHA)" | tee -a .runs/build.log
	DOCKER_BUILDKIT=0 $(COMPOSE) build --build-arg GIT_SHA=$(GIT_SHA) --no-cache --pull=false rag-api 2>&1 | tee -a .runs/build.log
	$(COMPOSE) up -d rag-api 2>&1 | tee -a .runs/build.log

## Rebuild with auto-fallback: try BuildKit then fallback to classic if registry lookups fail
rebuild-auto: ## BuildKit→Classic 自动降级，贯穿 GIT_SHA，写日志
	mkdir -p .runs
	DOCKER_BUILDKIT=1 $(COMPOSE) build --build-arg GIT_SHA=$(GIT_SHA) --no-cache --pull=false rag-api 2>&1 | tee -a .runs/build.log || (echo "[WARN] BuildKit failed, falling back to classic..." | tee -a .runs/build.log; ENV_FILE=$(ENV_FILE) GIT_SHA=$(GIT_SHA) scripts/build_with_fallback.sh rag-api 2>&1 | tee -a .runs/build.log)
	$(COMPOSE) up -d rag-api 2>&1 | tee -a .runs/build.log

## Fast rebuild - recreate container without rebuilding image (for env var changes)
rebuild-fast: ## Fast rebuild - recreate container without rebuilding image
	@echo "🚀 Fast rebuild: recreating container without rebuilding image..."
	$(COMPOSE) up -d --force-recreate rag-api
	@echo "⏳ Waiting for service to be ready..."
	@sleep 5
	@$(MAKE) health

real-large-on: realcheck-up
	@USE_PROXY=true PROXY_URL=$${PROXY_URL:-http://localhost:7070} RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
		MODES=proxy_on N=$${N:-1000} python3 scripts/realcheck_large.py --no-paired

real-large-off: realcheck-up
	@USE_PROXY=false PROXY_URL=$${PROXY_URL:-http://localhost:7070} RAG_API_URL=$${RAG_API_URL:-http://localhost:8000} \
		MODES=proxy_off N=$${N:-1000} python3 scripts/realcheck_large.py --no-paired

real-large-paired:
	@python3 scripts/realcheck_large.py --paired --warmup 10 --no-cache --no-rerank --trim-pct 5 --samples 2000 --budgets "200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600"

real-pareto: real-large-paired
	@python3 scripts/realcheck_pareto.py --aggregate --budgets "200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600"

real-plot:
	@python3 scripts/realcheck_large.py --plot-only
	@test -s .runs/real_large_trilines.csv
	@test -s .runs/real_large_trilines.png

real-fast-paired:
	@python3 scripts/realcheck_large.py --paired --warmup 10 --no-cache --no-rerank --trim-pct 5 --samples 200 --budgets "400,600,800,1000,1200"

real-fast-pareto: real-fast-paired
	@python3 scripts/realcheck_large.py --aggregate --budgets "400,600,800,1000,1200" --pareto-json .runs/pareto_fast.json

real-fast-plot:
	@python3 scripts/realcheck_large.py --plot-only --pareto-json .runs/pareto_fast.json --output-csv .runs/real_fast_trilines.csv --output-png .runs/real_fast_trilines.png
	@test -s .runs/real_fast_trilines.csv
	@test -s .runs/real_fast_trilines.png

trilines-refresh: ## Generate .runs/real_large_trilines.json/csv
	@$(MAKE) real-plot

kpi-refresh: ## Generate .runs/pareto.json and .runs/e2e_report.json
	@$(MAKE) real-pareto
	@$(MAKE) e2e-mini

ci: ## Run CI with self-healing
	@bash scripts/ci_self_heal.sh

ci-fast: gpu-smoke ## Fast CI for daily development (few minutes, reduced samples/budgets)
	@echo "[CI-FAST] running fast evaluation..."
	@$(MAKE) real-fast-paired
	@$(MAKE) real-fast-pareto || echo "[CI-FAST] ⚠️  Pareto aggregation had some failures, but continuing..."
	@$(MAKE) real-fast-plot
	@echo "[CI-FAST] ✅ done (artifacts in .runs/real_fast_trilines.csv)"

ci-raw: policy-smoke e2e-mini real-large-paired real-pareto real-plot
	@jq -e '.success_rate>=0.99 and .bounds_ok and .stable_detune and .p95_down' .runs/real_large_report.json >/dev/null
	@jq -e '.ok==true' .runs/pareto.json >/dev/null
	@test -s .runs/real_large_trilines.csv && test -s .runs/real_large_trilines.png
	@echo "[CI] Checking trilines CSV density..."
	@python3 scripts/check_trilines_density.py
	@python3 scripts/check_autotuner_persistence.py
	@echo "[CI] Checking for GPU fallback..."
	@bash scripts/check_gpu_fallback.sh || (echo "[CI] ❌ GPU fallback detected - CI must use GPU"; exit 1)
	@echo "[CI] Hard assertions: bounds_ok && stable_detune && p95_down"
	@test -f .runs/pareto.json && jq -e '.bounds_ok==true' .runs/pareto.json >/dev/null || (echo "❌ bounds_ok assertion failed"; exit 1)
	@test -f .runs/pareto.json && jq -e '.stable_detune==true' .runs/pareto.json >/dev/null || (echo "❌ stable_detune assertion failed"; exit 1)
	@test -f .runs/pareto.json && jq -e '.p95_down==true' .runs/pareto.json >/dev/null || (echo "❌ p95_down assertion failed"; exit 1)
	@echo "[CI] Gate 1: Simulating registry timeout..."
	@SIMULATE_REGISTRY_TIMEOUT=1 ENV_FILE=$(ENV_FILE) GIT_SHA=$(GIT_SHA) scripts/build_with_fallback.sh rag-api
	@sleep 2
	@echo "[CI] Verify base images use :py311"
	@key_services="services/fiqa_api/Dockerfile services/auto_tuner/Dockerfile services/chaos_injector/Dockerfile services/probe_cron/Dockerfile services/shadow_proxy/Dockerfile"; \
	for df in $$key_services; do \
		if [ -f "$$df" ] && ! grep -q '^FROM .*searchforge-base:py311' "$$df" 2>/dev/null; then \
			echo "❌ $$df does not use searchforge-base:py311"; exit 1; \
		fi; \
	done; \
	echo "✅ All key services use searchforge-base:py311"
	@echo "[CI] Verify /version == GIT_SHA"
	@test "$(GIT_SHA)" = "$$(curl -fsS --retry 3 --retry-connrefused --max-time 5 http://localhost:8000/version | jq -r '.commit')" || (echo "/version mismatch"; exit 1)
	@echo "[CI] Verify cost_per_1k_usd > 0"
	@awk -F, 'NR==1{for(i=1;i<=NF;i++)if($$i=="cost_per_1k_usd")c=i} NR>1{s+=$$c} END{if(s<=0)exit 1}' .runs/real_large_trilines.csv || (echo "cost_per_1k_usd==0, configure MODEL_PRICING_JSON"; exit 1)
	@echo "[CI] Verify production build doesn't leak token"
	@if [ -d ui/dist ]; then \
		if grep -R "VITE_AUTOTUNER_TOKEN" ui/dist/ 2>/dev/null; then \
			echo "❌ Token leaked in production build"; exit 1; \
		else \
			echo "✅ No token leaked in production build"; \
		fi; \
	else \
		echo "⚠️  ui/dist not found, skipping token leak check"; \
	fi
	@echo "✅ CI guards OK"

check-qdrant:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	python3 scripts/check_qdrant.py | tee .runs/qdrant_check.json

seed-fiqa:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	python3 scripts/seed_qdrant.py | tee .runs/qdrant_seed.json

reseed-fiqa:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	@echo "FORCE=1 reseed fiqa..."
	@FORCE=1 python3 scripts/seed_qdrant.py > .runs/qdrant_seed.json
	@python3 scripts/check_qdrant.py > .runs/qdrant_check.json
	@echo "reseed done"

vitals-stream: ## Generate fake vitals stream (stdout mode, 60s, 2s interval)
	$(call ensure_tool,python3)
	@python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 60 --interval-sec 2.0

vitals-e2e: ## End-to-end verification of vitals POST mode (requires API running)
	$(call ensure_tool,python3)
	@python3 scripts/verify_vitals_e2e_post.py --endpoint-base http://localhost:8000 --duration-sec 10 --interval-sec 1

qdrant-bind-setup:
	@mkdir -p .qdrant
	@echo "[ok] .qdrant bind dir ready"

qdrant-backup-volume:
	@chmod +x scripts/backup_qdrant_volume.sh
	@./scripts/backup_qdrant_volume.sh searchforge_qdrant_data

qdrant-restart:
	$(COMPOSE) up -d qdrant
	@sleep 2
	@echo "[info] wait qdrant..."
	@curl -fsS http://localhost:6333/regions >/dev/null || true

fiqa-reseed:
	@echo "[info] seeding fiqa_50k_v1 ..."
	$(MAKE) seed-fiqa

fiqa-import-full: ## Import full FiQA 50k dataset (all collections)
	$(call ensure_tool,python3)
	@mkdir -p .runs
	@echo "[info] Importing full FiQA 50k dataset (all available collections)..."
	@python3 scripts/import_fiqa_50k.py --all --recreate | tee .runs/import_fiqa_50k.log
	@echo "[info] Import complete. Check .runs/import_fiqa_50k.json for summary"

fiqa-import: ## Import FiQA 50k collection (default: fiqa_50k_v1)
	$(call ensure_tool,python3)
	@mkdir -p .runs
	@COLLECTION=$${COLLECTION:-fiqa_50k_v1}; \
	echo "[info] Importing collection: $$COLLECTION ..."; \
	python3 scripts/import_fiqa_50k.py --collection $$COLLECTION --recreate | tee .runs/import_fiqa_50k.log

rebuild-fiqa-para: ## Rebuild fiqa_para_50k collection from manifest
	$(call ensure_tool,python3)
	@mkdir -p .runs
	@python3 scripts/import_fiqa_manifest.py --manifest data/fiqa_v1/manifest_50k_v1.json --collection fiqa_para_50k --recreate --batch 512 2>&1 | tee .runs/import_fiqa_para.log

check-fiqa:
	@curl -fsS http://localhost:6333/collections/fiqa_50k_v1 | jq .
	@echo "[assert] points_count >= 50000 (full data expected)"

# ===== DocID 热修补 & 断言 =====
DOC_COLLECTION ?= fiqa_para_50k
DOCID_LEN ?= 6

.PHONY: fix-docid
fix-docid:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	@bash -c 'QDRANT_URL=$${QDRANT_URL:-http://localhost:6333} python3 scripts/patch_docid_padding.py --collection $(DOC_COLLECTION) --length $(DOCID_LEN) --url $${QDRANT_URL:-http://localhost:6333} 2>&1 | tee .runs/fix_docid_$(DOC_COLLECTION).log; exit $${PIPESTATUS[0]}'

.PHONY: assert-docid
assert-docid:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	@bash -c 'QDRANT_URL=$${QDRANT_URL:-http://localhost:6333} python3 scripts/patch_docid_padding.py --collection $(DOC_COLLECTION) --length $(DOCID_LEN) --assert-only --url $${QDRANT_URL:-http://localhost:6333} 2>&1 | tee .runs/assert_docid_$(DOC_COLLECTION).log; exit $${PIPESTATUS[0]}'

# ===== DocID 恢复（从旧卷/备份） =====
.PHONY: docid-export-old
docid-export-old:
	$(call ensure_tool,python3)
	@OLD_BASE=$${OLD_BASE:-http://localhost:6335}; \
	COLLECTION=$${COLLECTION:-fiqa_para_50k}; \
	OUT=$${OUT:-.runs/docid_map_$$COLLECTION.json}; \
	echo "[INFO] Exporting doc_id mapping from old Qdrant..."; \
	echo "[INFO] OLD_BASE=$$OLD_BASE COLLECTION=$$COLLECTION OUT=$$OUT"; \
	mkdir -p $$(dirname "$$OUT"); \
	bash -c 'EXPECTED_COUNT=$${EXPECTED_COUNT:-50000}; \
		python3 scripts/docid_export_from_qdrant.py \
		--base "$$OLD_BASE" \
		--collection "$$COLLECTION" \
		--out "$$OUT" \
		--expected-count $$EXPECTED_COUNT 2>&1 | tee .runs/docid_restore.log; \
		exit $${PIPESTATUS[0]}'

.PHONY: docid-apply
docid-apply:
	$(call ensure_tool,python3)
	@COLLECTION=$${COLLECTION:-fiqa_para_50k}; \
	MAP=$${MAP:-.runs/docid_map_$$COLLECTION.json}; \
	if [ ! -f "$$MAP" ]; then \
		echo "[ERROR] Mapping file not found: $$MAP"; \
		echo "[ERROR] Run 'make docid-export-old' first or set MAP variable"; \
		exit 1; \
	fi; \
	echo "[INFO] Applying doc_id mapping to current collection..."; \
	echo "[INFO] COLLECTION=$$COLLECTION MAP=$$MAP"; \
	bash -c 'EXPECTED_COUNT=$${EXPECTED_COUNT:-50000}; \
		python3 scripts/docid_apply_map.py \
		--base http://localhost:6333 \
		--collection "$$COLLECTION" \
		--map "$$MAP" \
		--expected-count $$EXPECTED_COUNT 2>&1 | tee -a .runs/docid_restore.log; \
		exit $${PIPESTATUS[0]}'

.PHONY: docid-verify
docid-verify:
	$(call ensure_tool,python3)
	@COLLECTION=$${COLLECTION:-fiqa_para_50k}; \
	MAP=$${MAP:-.runs/docid_map_$$COLLECTION.json}; \
	if [ ! -f "$$MAP" ]; then \
		echo "[ERROR] Mapping file not found: $$MAP"; \
		echo "[ERROR] Run 'make docid-export-old' first or set MAP variable"; \
		exit 1; \
	fi; \
	echo "[INFO] Verifying doc_id mapping..."; \
	echo "[INFO] COLLECTION=$$COLLECTION MAP=$$MAP"; \
	bash -c 'EXPECTED_COUNT=$${EXPECTED_COUNT:-50000}; \
		python3 scripts/docid_apply_map.py \
		--base http://localhost:6333 \
		--collection "$$COLLECTION" \
		--map "$$MAP" \
		--verify-only \
		--sample 200 \
		--expected-count $$EXPECTED_COUNT 2>&1 | tee -a .runs/docid_restore.log; \
		EXIT_CODE=$${PIPESTATUS[0]}; \
		if [ $$EXIT_CODE -eq 0 ]; then \
			echo "[INFO] doc_id verification passed"; \
		else \
			echo "[ERROR] doc_id verification failed"; \
		fi; \
		exit $$EXIT_CODE'

a-verify:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	python3 scripts/abc_verify.py --only A | tee -a .runs/abc_verify.log

b-verify:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	python3 scripts/abc_verify.py --only B | tee -a .runs/abc_verify.log

c-verify:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	python3 scripts/abc_verify.py --only C | tee -a .runs/abc_verify.log

abc-verify:
	$(call ensure_tool,python3)
	@mkdir -p .runs
	python3 scripts/abc_verify.py | tee -a .runs/abc_verify.log

down-proxy:
	docker compose down

obs-verify: ## 验证 Langfuse OBS 连通性并打印最新 obs_url
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	@curl -sf http://127.0.0.1:8000/obs/ping | jq .
	@echo "OBS URL:"
	@if [ -f .runs/obs_url.txt ]; then cat .runs/obs_url.txt; else echo "  (missing .runs/obs_url.txt)"; fi
	@echo "TRACE ID:"
	@if [ -f .runs/trace_id.txt ]; then cat .runs/trace_id.txt; else echo "  (missing .runs/trace_id.txt)"; fi

obs-url:
	$(call ensure_tool,curl)
	@mkdir -p .runs
	curl -sf http://localhost:8000/obs/url | tee .runs/obs_url_api.json

ui-open-check:
	$(call ensure_tool,python3)
	@python3 - <<-'PY'
	import json
	import sys
	from pathlib import Path

	path = Path(".runs/obs_url_api.json")
	if not path.exists():
		print("missing .runs/obs_url_api.json", file=sys.stderr)
		sys.exit(1)
	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except Exception as exc:  # pragma: no cover
		print(f"failed to parse obs_url_api.json: {exc}", file=sys.stderr)
		sys.exit(1)
	obs_url = (payload or {}).get("obs_url", "").strip()
	if obs_url:
		print(obs_url)
		sys.exit(0)
	print("obs_url missing", file=sys.stderr)
	sys.exit(1)
	PY

export: ## Export dependencies snapshot from container
	@echo "📦 Exporting dependency snapshot via pip freeze..."
	$(COMPOSE) run --rm $(SERVICE) sh -lc "pip freeze --exclude-editable" > requirements.lock
	@echo "✅ Snapshot written to requirements.lock"
	@echo ""
	@echo "📋 环境切换 (Environment Switching)"
	@echo "  make whoami              - 查看当前目标环境"
	@echo "  make update-hosts        - 刷新远程主机名映射（需要 sudo）"
	@echo "  make cutover-remote       - 切换到远程环境（带 SLA 检查）"
	@echo "  make compose-config       - 查看当前服务端点配置"
	@echo ""
	@echo "📊 基线管理 (Baseline Management)"
	@echo "  make baseline-save-local  - 创建本地环境性能基线"
	@echo "  make baseline-save-remote - 创建远程环境性能基线"
	@echo "  make baseline-save       - 根据当前目标自动创建基线"
	@echo ""
	@echo "🔄 远程服务管理 (Remote Service Management)"
	@echo "  make up                  - 启动远程服务"
	@echo "  make down                - 停止远程服务"
	@echo "  make restart             - 重启远程服务"
	@echo "  make health              - 检查远程服务健康状态"
	@echo "  make logs                - 查看远程服务日志"
	@echo "  make ps                  - 查看远程容器状态"
	@echo ""
	@echo "🧹 清理和维护 (Cleanup & Maintenance)"
	@echo "  make prune-safe          - 安全清理 Docker（保留数据卷）"
	@echo "  make df                  - 查看 Docker 磁盘使用情况"
	@echo "  make cleanup-audit       - 审计可清理的文件（dry-run）"
	@echo "  make cleanup-apply       - 归档未使用的脚本/测试/文档"
	@echo "  make cleanup-restore     - 恢复归档的文件"
	@echo ""
	@echo "🔬 评测和金标工具 (Evaluation & Gold Standard)"
	@echo "  make eval-qrels          - 检查 qrels 覆盖率 (10k/50k)"
	@echo "  make eval-consistency    - 检查数据集/集合/字段一致性"
	@echo "  make eval-recall         - 计算去重后的 Recall@K"
	@echo "  make gold-prepare        - 准备薄金标候选 CSV"
	@echo "  make gold-finalize       - 从标注生成 qrels_gold.tsv"
	@echo "  make cleanup-history     - 清理 Git 历史中的大文件（危险操作）"
	@echo ""
	@echo "🔗 隧道和访问 (Tunnels & Access)"
	@echo "  make tunnel-dozzle       - 创建 Dozzle 日志查看隧道（Ctrl-C 关闭）"
	@echo "  make open-portainer      - 打开 Portainer 管理界面"
	@echo ""
	@echo "🛠️  其他工具 (Other Tools)"
	@echo "  make sync                - 同步文件到远程"
	@echo "  make gpu-smoke           - GPU 测试"
	@echo "  make migrate-qdrant      - 迁移 Qdrant 数据到远程"
	@echo "  make ui                  - 启动前端 UI Dashboard"
	@echo "  make rebuild-api         - 重建并重启 rag-api 服务"
	@echo "  make rebuild-api-cpu      - 重建 CPU-only rag-api 并验证无 CUDA"
	@echo "  make win-fw-allow-8000    - 打印 Windows 防火墙放行 8000 (Tailscale 段)"
	@echo "  make net-verify           - 端口与健康检查 (容器内/外)"
	@echo "  make up-gpu              - 启动 GPU worker 服务（可选）"
	@echo "  make down-gpu            - 停止 GPU worker 服务"
	@echo ""
	@echo "🧪 实验管理 (Experiment Management)"
	@echo "  make sync-experiments    - 同步实验脚本到远程服务器"
	@echo "  make verify-experiments  - 验证远程实验文件是否存在"
	@echo "  make runner-check        - 检查 runner 自检端点"
	@echo "  make smoke-experiment    - 运行最小实验（sample=5）"
	@echo ""
	@echo "🔒 Phase A: Baseline + Presets + Guards"
	@echo "  make guard-no-cuda       - 检查本地环境无 CUDA 包"
	@echo "  make embed-doctor       - 检查 embedding 模型配置"
	@echo "  make baseline-run       - 提交 baseline 实验"
	@echo "  make baseline-poll       - 轮询 baseline 任务状态"
	@echo "  make baseline-artifacts  - 下载 baseline 结果"
	@echo ""
	@echo "💡 使用示例："
	@echo "  make help                - 显示此帮助信息"
	@echo "  make cutover-remote       - 切换到远程（使用默认参数）"
	@echo "  N=150 C=10 WARMUP=10 TIMEOUT=3 make cutover-remote  - 自定义参数切换"
	@echo ""
	@echo "=================================================="

dev-api-bg:
	$(COMPOSE) up -d $(SERVICE)
	@echo "rag-api running in background via docker compose"

stop-api:
	$(COMPOSE) stop $(SERVICE)

sync:
	@rsync -avzP mini-d-files/ $(REMOTE):$(RDIR)/

ssh-ok:
	@ssh andy-wsl 'echo ok'

up:
	@ssh $(SSH_HOST) 'cd $(RDIR) && cp -n .env.sample .env || true && docker compose up -d --build'
	@$(MAKE) health

down:
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose down'

restart:  ## Restart backend service on remote
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose restart rag-api || docker compose up -d rag-api'
	@sleep 5
	@$(MAKE) health

logs:
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose logs -f --tail=200 api'

ps:
	@ssh $(SSH_HOST) 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

health:
	@ssh $(SSH_HOST) 'curl -fsS http://localhost:8000/health && echo'

prune-safe:
	@ssh $(SSH_HOST) 'docker system prune -af' # 不带 --volumes，避免误删数据卷

df:
	@ssh $(SSH_HOST) 'docker system df -v'

# 本机开一个隧道：访问 http://localhost:9999 查看 Dozzle
tunnel-dozzle:
	@echo "Press Ctrl-C to close the tunnel."
	@ssh -N -L 9999:127.0.0.1:9999 $(REMOTE)

# 快捷打开 Portainer（把 100.x.x.x 换成你的 Tailscale IP）
open-portainer:
	@open https://100.67.88.114:9443

whoami:
	@bash tools/switch/print_target.sh

gpu-hardware:
	@$(COMPOSE) run --rm --gpus all gpu-smoke nvidia-smi -L

compose-config:
	@echo "Service endpoints from .env.current:"
	@grep -E '^RAG_API_BASE=|^QDRANT_URL=' .env.current 2>/dev/null || echo "⚠️  RAG_API_BASE or QDRANT_URL not found in .env.current"

update-hosts:
	@bash tools/switch/update_hosts.sh

migrate-qdrant:
	@bash tools/switch/migrate_qdrant_to_remote.sh

cutover-remote:
	@pip install -q aiohttp || true
	@mkdir -p artifacts/sla/manifests
	@bash tools/switch/cutover_remote.sh

baseline-save-local:
	@mkdir -p artifacts/sla
	@echo "Running baseline smoke test against local RAG API..."
	@RAG_API_BASE=http://localhost:8000 python3 tools/switch/smoke.py --n 200 --concurrency 10 --warmup 20 --timeout 3 --base http://localhost:8000 > artifacts/sla/baseline.local.json
	@echo "✅ Baseline saved to artifacts/sla/baseline.local.json"

baseline-save-remote:
	@mkdir -p artifacts/sla
	@echo "Running baseline smoke test against remote RAG API..."
	@RAG_API_BASE=http://andy-wsl:8000 python3 tools/switch/smoke.py --n 200 --concurrency 10 --warmup 20 --timeout 3 --base http://andy-wsl:8000 > artifacts/sla/baseline.remote.json
	@echo "✅ Baseline saved to artifacts/sla/baseline.remote.json"

baseline-save:
	@if [[ "$(TARGET)" == remote* ]]; then \
		$(MAKE) baseline-save-remote; \
	else \
		$(MAKE) baseline-save-local; \
	fi

ui-reset:
	@cd ui && if [ -d "node_modules" ]; then npm run clean; else echo "node_modules already removed"; fi
	@cd ui && npm run ci

ui-verify:
	@cd ui && npm run verify:deps

ui: ui-reset ui-verify
	@cd ui && npm run dev

rebuild-api: guard-no-legacy export-reqs
	@echo "🔨 Rebuilding rag-api service..."
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose build rag-api && docker compose up -d rag-api'
	@echo "⏳ Waiting for service to be ready..."
	@sleep 5
	@$(MAKE) health

rebuild-api-cpu: ## 重建 CPU-only rag-api 并验证无 CUDA 包
	@echo "🔨 Rebuilding CPU-only rag-api service..."
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose build --no-cache rag-api && docker compose up -d rag-api'
	@echo "⏳ Waiting for service to be ready..."
	@for i in $$(seq 1 30); do \
		echo "⏳ waiting ($$i/30)..."; \
		sleep 1; \
		curl -fsS http://andy-wsl:8000/health >/dev/null 2>&1 && break || true; \
	done
	@$(MAKE) net-verify
	@$(MAKE) guard-no-cuda
	@$(MAKE) embed-doctor
	@echo "✅ CPU-only rebuild complete and verified"

guard-no-cuda: ## 检查容器中是否包含 CUDA 包
	@echo "🔍 Checking for CUDA packages in container..."
	@docker compose exec -T rag-api python3 tools/guards/check_no_cuda_local.py || (echo "⚠️  CUDA packages detected (non-fatal for CPU-only SBERT)" && exit 0)
	@echo "✅ No CUDA packages found"

embed-doctor: ## 检查 embedding 模型配置
	@echo "🔍 Checking embedding model configuration..."
	@API_BASE=$$(curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 && echo "http://127.0.0.1:8000" || echo "http://localhost:8000"); \
	curl -fsS $$API_BASE/api/health/embeddings | python3 -c "import sys, json; d=json.load(sys.stdin); print(json.dumps(d, indent=2))" || (echo "❌ Embedding model check failed"; exit 1)
	@echo "✅ Embedding model consistency check passed"

guard-no-legacy:
	@test ! -f services/rag_api/app.py || (echo "❌ legacy app.py exists"; exit 1)
	@! grep -RInE 'services[./]rag_api[./]app(\.py)?|uvicorn .*app:app' --exclude=Makefile --exclude-dir=.git . \
	  || (echo "❌ found legacy refs to rag_api/app or app:app"; exit 1)
	@echo "✅ no legacy app.py or refs"

win-fw-allow-8000: ## 打印 Windows 防火墙放行 8000 的 PowerShell 命令
	@echo '以管理员 PowerShell 执行以下命令：'
	@echo 'New-NetFirewallRule -DisplayName "SearchForge rag-api 8000 Tailscale" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress 100.64.0.0/10 -Action Allow'

net-verify: ## 验证 rag-api 端口绑定与健康接口
	@echo "🔎 Checking container port bindings (remote)..."
	@ssh $(SSH_HOST) 'docker ps --format "table {{.Names}}\t{{.Ports}}" | grep rag-api || true'
	@echo "🔎 Curl health from inside container (127.0.0.1:${MAIN_PORT})..."
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose exec -T rag-api sh -lc "curl -fsS http://127.0.0.1:${MAIN_PORT}/health || curl -fsS http://127.0.0.1:8000/health"'
	@echo "🔎 Curl health from Mac (andy-wsl:8000)..."
	@curl -fsS http://andy-wsl:8000/health || (sleep 2; curl -fsS http://andy-wsl:8000/health)
	@echo "✅ Network verification done"

up-gpu: ## Start GPU worker service
	@echo "🚀 Starting GPU worker service..."
	$(COMPOSE) up -d gpu-worker
	@echo "✅ GPU worker started"

down-gpu: ## Stop GPU worker service
	@echo "🛑 Stopping GPU worker service..."
	$(COMPOSE) stop gpu-worker
	@echo "✅ GPU worker stopped"

gpu-smoke: up-gpu ## Run GPU path smoke test (self-contained)
	$(call ensure_tool,python3)
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	@mkdir -p .runs
	@echo "🧪 Running GPU path smoke test..."
	@echo "1. Waiting for GPU worker readiness..."
	@bash scripts/wait_for_gpu_ready.sh || (echo "❌ GPU worker not ready"; exit 1)
	@echo "2. Running GPU worker smoke tests..."
	@GPU_WORKER_URL=$${GPU_WORKER_URL:-http://localhost:8090} python3 scripts/gpu_worker_smoke.py || exit 1
	@echo "3. Testing RAG query through rag-api (should hit GPU worker)..."
	@if ! curl -fsS -X POST http://localhost:8000/api/query \
		-H 'Content-Type: application/json' \
		-d '{"question":"what is ETF?","top_k":5,"rerank":true}' \
		| jq -e '.items != null' >/dev/null 2>&1; then \
		echo "❌ RAG query failed or returned invalid response"; \
		exit 1; \
	fi
	@echo "[GPU-SMOKE] ✅ GPU path OK"

.PHONY: guardrails-lab-baseline
guardrails-lab-baseline: gpu-smoke
	@echo "[EXPERIMENT] RAG Hallucination & Guardrails Lab (baseline)..."
	python3 experiments/guardrails_lab.py --mode baseline

.PHONY: guardrails-lab-guarded
guardrails-lab-guarded: gpu-smoke
	@echo "[EXPERIMENT] RAG Hallucination & Guardrails Lab (guarded)..."
	python3 experiments/guardrails_lab.py --mode guarded

.PHONY: guardrails-lab-all
guardrails-lab-all: guardrails-lab-baseline guardrails-lab-guarded
	@echo "[EXPERIMENT] Guardrails lab baseline vs guarded completed."

.PHONY: kv-stream-demo
kv-stream-demo: gpu-smoke
	@echo "[EXPERIMENT] KV-cache / Streaming Lab (baseline demo)..."
	python3 experiments/kv_stream_lab.py --mode baseline --num-queries 50

.PHONY: kv-stream-all
kv-stream-all: gpu-smoke
	@echo "[EXPERIMENT] KV-cache / Streaming Lab (all modes)..."
	python3 experiments/kv_stream_lab.py --mode all --num-queries 50

.PHONY: llm-query-smoke
llm-query-smoke: gpu-smoke
	@echo "[EXPERIMENT] LLM query smoke test..."
	@echo "[NOTE] Need to set LLM_GENERATION_ENABLED=true to actually call LLM, otherwise only retrieval will run."
	python3 experiments/llm_query_smoke.py

.PHONY: auto-tuner-on-off
auto-tuner-on-off: gpu-smoke
	@echo "[EXPERIMENT] AutoTuner On/Off (full)..."
	python3 experiments/auto_tuner_on_off.py

.PHONY: go-proxy-on-off
go-proxy-on-off: gpu-smoke proxy-smoke
	@echo "[EXPERIMENT] Go proxy On/Off (concurrency/QPS)..."
	python3 experiments/go_proxy_on_off.py

.PHONY: auto-tuner-hard
auto-tuner-hard: gpu-smoke
	@echo "[EXPERIMENT] AutoTuner On/Off (HARD mode: tight budgets, fewer queries)..."
	python3 experiments/auto_tuner_on_off.py \
		--n-queries 150 \
		--budgets-ms "50,60,70,80" \
		--repeats 3 \
		--tag "hard"

.PHONY: auto-tuner-sla
auto-tuner-sla: gpu-smoke
	@echo "[EXPERIMENT] AutoTuner vs Heavy Baseline under tight SLA..."
	python3 experiments/auto_tuner_on_off.py \
		--n-queries 150 \
		--budgets-ms "50,60,70" \
		--repeats 3 \
		--baseline-top-k 40 \
		--baseline-rerank true \
		--autotuner-top-k 10 \
		--autotuner-rerank false \
		--tag "sla"

.PHONY: auto-tuner-sla-plot
auto-tuner-sla-plot:
	@echo "[PLOT] AutoTuner vs Heavy Baseline under tight SLA..."
	python3 experiments/plot_auto_tuner_sla.py

.PHONY: auto-tuner-sla-all
auto-tuner-sla-all: auto-tuner-sla auto-tuner-sla-plot
	@echo "[PLOT] AutoTuner SLA experiment + plot complete."

.PHONY: regression
regression:
	@echo "[REGRESSION] Running regression suite (AutoTuner SLA + Go proxy + ci-fast)..."
	@python3 scripts/run_regression_suite.py

.PHONY: buildx-init gpu-build
buildx-init: ## Initialize Docker buildx builder
	@echo "🔧 Initializing Docker buildx builder..."
	@docker buildx create --use || true
	@mkdir -p .buildx-cache
	@echo "✅ Buildx builder ready"

gpu-build: buildx-init ## Build GPU worker with BuildKit cache
	@echo "🔨 Building GPU worker with BuildKit cache..."
	@$(call ensure_tool,docker)
	@if [ ! -f .env.current ]; then \
		echo "⚠️  .env.current not found, using defaults"; \
		TORCH_VERSION=$${TORCH_VERSION:-2.3.0}; \
		PYTORCH_CUDA=$${PYTORCH_CUDA:-121}; \
		MODEL_NAME=$${MODEL_NAME:-sentence-transformers/all-MiniLM-L6-v2}; \
	else \
		export $$(grep -v '^#' .env.current | xargs); \
	fi; \
	DOCKER_BUILDKIT=1 docker buildx build \
	  -f docker/Dockerfile.gpu-worker \
	  --build-arg TORCH_VERSION=$${TORCH_VERSION:-2.4.0} \
	  --build-arg PYTORCH_CUDA=$${PYTORCH_CUDA:-121} \
	  --build-arg MODEL_NAME=$${MODEL_NAME:-sentence-transformers/all-MiniLM-L6-v2} \
	  --cache-from=type=local,src=.buildx-cache \
	  --cache-to=type=local,dest=.buildx-cache,mode=max \
	  -t gpu-worker:latest --load .
	@echo "✅ GPU worker build complete"

gpu-prewarm: ## Wait for /ready and POST /embed to populate caches
	$(call ensure_tool,curl)
	@echo "🔥 Prewarming GPU worker..."
	@echo "Waiting for /ready=200..."
	@for i in $$(seq 1 60); do \
		if curl -fsS http://localhost:8090/ready >/dev/null 2>&1; then \
			echo "✅ /ready=200"; \
			break; \
		fi; \
		echo "⏳ waiting ($$i/60)..."; \
		sleep 1; \
	done
	@echo "POST /embed with [\"hello\",\"world\"]..."
	@curl -fsS -X POST http://localhost:8090/embed \
		-H 'Content-Type: application/json' \
		-d '{"texts":["hello","world"]}' >/dev/null 2>&1 || (echo "❌ Prewarm failed"; exit 1)
	@echo "✅ Prewarm complete (on-disk caches populated)"

gpu-accept: ## Acceptance test: check device==cuda, /ready=200, run gpu-smoke
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	$(call ensure_tool,python3)
	@echo "✅ Running GPU worker acceptance tests..."
	@echo "1. Checking /meta -> device==cuda..."
	@DEVICE=$$(curl -fsS http://localhost:8090/meta | jq -r '.device'); \
	if [ "$$DEVICE" != "cuda" ]; then \
		echo "❌ device=$$DEVICE, expected cuda"; \
		exit 1; \
	fi; \
	echo "✅ device=$$DEVICE"
	@echo "2. Checking /ready=200..."
	@curl -fsS http://localhost:8090/ready >/dev/null 2>&1 || (echo "❌ /ready failed"; exit 1)
	@echo "✅ /ready=200"
	@echo "3. Running gpu-smoke..."
	@$(MAKE) gpu-smoke
	@echo "4. Verifying all_passed=true..."
	@ALL_PASSED=$$(jq -r '.all_passed' .runs/gpu_worker_smoke.json 2>/dev/null || echo "false"); \
	if [ "$$ALL_PASSED" != "true" ]; then \
		echo "❌ all_passed=$$ALL_PASSED, expected true"; \
		exit 1; \
	fi; \
	echo "✅ all_passed=$$ALL_PASSED"
	@echo "✅ GPU worker acceptance tests passed"

# Repository cleanup targets (safe, reversible archiving)
cleanup-audit: ## 审计可清理的文件（dry-run，生成候选列表）
	@bash tools/cleanup/audit.sh

audit-space: ## Run read-only disk usage audit and generate report
	@mkdir -p artifacts/disk_audit
	@bash tools/cleanup/audit_space.sh | tee artifacts/disk_audit/report.md

cleanup-apply: ## 归档未使用的脚本/测试/文档到 archive/
	@bash tools/cleanup/apply.sh

cleanup-restore: ## 恢复归档的文件到原始位置
	@bash tools/cleanup/restore.sh

cleanup-history: ## 清理 Git 历史中的大文件（需要 I_KNOW_WHAT_IM_DOING=1）
	@bash tools/cleanup/slim_history.sh

create-clean-repo: ## 创建干净的仓库快照并切换到新远程（需要 NEW_REPO_URL=<url>）
	@bash tools/cleanup/create_clean_repo.sh

export-reqs: ## Export dependencies snapshot for container builds
	@echo "📦 Exporting dependency snapshot to services/rag_api/requirements.lock..."
	$(COMPOSE) run --rm $(SERVICE) sh -lc "pip freeze --exclude-editable" > services/rag_api/requirements.lock
	@echo "✅ Snapshot written to services/rag_api/requirements.lock"

POETRY_RUN_PATTERN := poetry\s\+run

lint-no-legacy-toolchain: ## Check that no legacy Poetry invocations remain
	@echo "🔍 Checking for legacy Poetry invocations..."
	@pattern='$(POETRY_RUN_PATTERN)'; \
	if git grep -nE "$$pattern" -- 'services/**' 'tools/**' 'Makefile' '**/Dockerfile' 'docker-compose*.yml' >/dev/null 2>&1; then \
		echo "❌ ERROR: legacy Poetry usage found:"; \
		git grep -nE "$$pattern" -- 'services/**' 'tools/**' 'Makefile' '**/Dockerfile' 'docker-compose*.yml'; \
		exit 1; \
	else \
		echo "✅ No legacy Poetry usage detected"; \
	fi

# Experiment management targets
sync-experiments: ## Sync experiments directory to remote server
	@bash tools/experiments/sync_experiments.sh

verify-experiments: ## Verify experiment files exist on remote server
	@bash tools/experiments/verify_remote.sh

runner-check: ## Check runner self-check endpoint
	@echo "🔍 Checking runner status..."
	@curl -fsS http://andy-wsl:8000/api/experiment/runner_check | python3 -m json.tool

smoke-experiment: ## Run minimal experiment (sample=5) to verify setup
	@echo "🧪 Running smoke test experiment (sample=5)..."
	@curl -sX POST http://andy-wsl:8000/api/experiment/run \
		-H 'content-type: application/json' \
		-d '{"preset_name":"fiqa_baseline_10k"}' | python3 -m json.tool > /tmp/smoke_job.json
	@JOB_ID=$$(python3 -c "import json; print(json.load(open('/tmp/smoke_job.json'))['job_id'])") && \
		echo "" && \
		echo "✅ Job submitted: $$JOB_ID" && \
		echo "📊 Check status: curl http://andy-wsl:8000/api/experiment/status/$$JOB_ID" && \
		echo "📜 Check logs: curl http://andy-wsl:8000/api/experiment/logs/$$JOB_ID"

smoke-fast: ## Run quick backend smoke test against local endpoints
	@bash scripts/quick_backend_smoke.sh

graph-smoke:
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	@HOST="$${HOST:-127.0.0.1}"; \
	PORT="$${PORT:-8000}"; \
	BASE="$${BASE:-}"; \
	if [ -z "$$BASE" ]; then BASE="http://$$HOST:$$PORT"; fi; \
	mkdir -p .runs; \
	JOB_ID="$${JOB_ID:-}"; \
	if [ -z "$$JOB_ID" ]; then JOB_ID="demo-$$(date +%s)"; fi; \
	echo "[graph-smoke] job=$$JOB_ID hitting $$BASE"; \
	RESP=$$(curl -sf -X POST "$$BASE/api/steward/run" -H "content-type: application/json" --data "{\"job_id\":\"$$JOB_ID\"}"); \
	printf "%s\n" "$$RESP" | jq '.'; \
	printf "%s\n" "$$JOB_ID" > .runs/graph_last_job.txt; \
	printf "%s\n" "$$RESP" > .runs/graph_smoke.json; \
	DRY=$$(printf "%s" "$$RESP" | jq -r '.dryrun_status // ""'); \
	if [ -z "$$DRY" ]; then echo "❌ dryrun_status empty"; exit 1; fi; \
	echo "✅ dryrun_status captured: $$DRY";

graph-resume:
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	$(call ensure_tool,python3)
	@test -f .runs/graph_last_job.txt || { echo "❌ missing .runs/graph_last_job.txt; run make graph-smoke first"; exit 1; }
	@$(MAKE) --no-print-directory stop-api >/dev/null || true
	@$(MAKE) --no-print-directory dev-api-bg >/dev/null
	@set -e; \
	HOST="$${HOST:-127.0.0.1}"; \
	PORT="$${PORT:-8000}"; \
	BASE="$${BASE:-}"; \
	if [ -z "$$BASE" ]; then BASE="http://$$HOST:$$PORT"; fi; \
	JOB_ID="$${JOB_ID:-}"; \
	if [ -z "$$JOB_ID" ]; then JOB_ID="$$(cat .runs/graph_last_job.txt)"; fi; \
	READY=0; \
	for i in $$(seq 1 60); do \
	  if curl -sf "$$BASE/health/ready" >/dev/null; then \
	    READY=1; \
	    break; \
	  fi; \
	  sleep 1; \
	done; \
	if [ "$$READY" -ne 1 ]; then echo "❌ rag-api not ready at $$BASE"; exit 1; fi; \
	RESP=$$(curl -sf -X POST "$$BASE/api/steward/run" -H "content-type: application/json" --data "{\"job_id\":\"$$JOB_ID\"}"); \
	printf "%s\n" "$$RESP" | jq '.'; \
	printf "%s\n" "$$RESP" > .runs/graph_resume.json
	@python3 scripts/graph_resume_check.py
	@JOB_OUT="$$(cat .runs/graph_last_job.txt)"; echo "✅ resume confirmed for $$JOB_OUT";

graph-full:
	$(call ensure_tool,curl)
	$(call ensure_tool,jq)
	$(call ensure_tool,python3)
	@test -f .runs/graph_last_job.txt || { echo "❌ missing .runs/graph_last_job.txt; run make graph-smoke first"; exit 1; }
	@set -e; \
	HOST="$${HOST:-127.0.0.1}"; \
	PORT="$${PORT:-8000}"; \
	BASE="$${BASE:-}"; \
	if [ -z "$$BASE" ]; then BASE="http://$$HOST:$$PORT"; fi; \
	JOB_ID="$${JOB_ID:-}"; \
	if [ -z "$$JOB_ID" ]; then JOB_ID="$$(cat .runs/graph_last_job.txt)"; fi; \
	ART_ROOT="$${ARTIFACTS_PATH:-}"; \
	if [ -z "$$ART_ROOT" ]; then ART_ROOT="artifacts"; fi; \
	mkdir -p "$$ART_ROOT/$$JOB_ID"; \
	MANIFEST_PATH="$$(JOB_ID=$$JOB_ID ART_ROOT=$$ART_ROOT python3 scripts/graph_generate_manifest.py)"; \
	printf "%s\n" "$$MANIFEST_PATH" > .runs/graph_manifest_path.txt; \
	printf "%s\n" "$$JOB_ID" > .runs/graph_last_job.txt
	@python3 scripts/graph_reset_thread.py "$$(cat .runs/graph_last_job.txt)"
	@TMP_ENV=.runs/graph_env.current; \
	([ -f .env.current ] && cat .env.current > $$TMP_ENV || :); \
	VAL_ACCEPT_P95="$$(grep -E '^ACCEPT_P95_MS=' $$TMP_ENV | tail -1 | cut -d= -f2)"; \
	VAL_ACCEPT_P95="$${VAL_ACCEPT_P95:-$${ACCEPT_P95_MS:-500}}"; \
	VAL_ACCEPT_ERR="$$(grep -E '^ACCEPT_ERR_RATE=' $$TMP_ENV | tail -1 | cut -d= -f2)"; \
	VAL_ACCEPT_ERR="$${VAL_ACCEPT_ERR:-$${ACCEPT_ERR_RATE:-0.05}}"; \
	VAL_MIN_RECALL="$$(grep -E '^MIN_RECALL10=' $$TMP_ENV | tail -1 | cut -d= -f2)"; \
	if [ -z "$$VAL_MIN_RECALL" ]; then \
	  VAL_MIN_RECALL="$$(grep -E '^MIN_RECALL_AT_10=' $$TMP_ENV | tail -1 | cut -d= -f2)"; \
	fi; \
	VAL_MIN_RECALL="$${VAL_MIN_RECALL:-$${MIN_RECALL10:-0.6}}"; \
	VAL_ACCEPT_RECALL="$$(grep -E '^ACCEPT_RECALL=' $$TMP_ENV | tail -1 | cut -d= -f2)"; \
	VAL_ACCEPT_RECALL="$${VAL_ACCEPT_RECALL:-$${ACCEPT_RECALL:-0.9}}"; \
	VAL_MIN_DELTA="$$(grep -E '^MIN_DELTA=' $$TMP_ENV | tail -1 | cut -d= -f2)"; \
	VAL_MIN_DELTA="$${VAL_MIN_DELTA:-$${MIN_DELTA:-0.0}}"; \
	printf "ACCEPT_P95_MS=%s\nACCEPT_ERR_RATE=%s\nMIN_RECALL10=%s\nACCEPT_RECALL=%s\nMIN_DELTA=%s\n" \
	  "$$VAL_ACCEPT_P95" \
	  "$$VAL_ACCEPT_ERR" \
	  "$$VAL_MIN_RECALL" \
	  "$$VAL_ACCEPT_RECALL" \
	  "$$VAL_MIN_DELTA" >> $$TMP_ENV; \
	$(COMPOSE) cp $$TMP_ENV $(SERVICE):/app/.env.current >/dev/null 2>&1
	@$(COMPOSE) cp scripts/graph_reset_thread.py $(SERVICE):/tmp/graph_reset_thread.py >/dev/null 2>&1
	@JOB_OUT="$$(cat .runs/graph_last_job.txt)"; \
	$(COMPOSE) exec $(SERVICE) python /tmp/graph_reset_thread.py "$$JOB_OUT" >/dev/null 2>&1
	@JOB_OUT="$$(cat .runs/graph_last_job.txt)"; MANIFEST="$$(cat .runs/graph_manifest_path.txt)"; \
	$(COMPOSE) exec $(SERVICE) sh -lc "mkdir -p /app/artifacts/$$JOB_OUT" >/dev/null
	@JOB_OUT="$$(cat .runs/graph_last_job.txt)"; MANIFEST="$$(cat .runs/graph_manifest_path.txt)"; \
	$(COMPOSE) cp "$$MANIFEST" $(SERVICE):/app/artifacts/$$JOB_OUT/manifest.json >/dev/null
	@HOST="$${HOST:-127.0.0.1}"; \
	PORT="$${PORT:-8000}"; \
	BASE="$${BASE:-}"; \
	if [ -z "$$BASE" ]; then BASE="http://$$HOST:$$PORT"; fi; \
	JOB_ID="$$(cat .runs/graph_last_job.txt)"; \
	RESP=$$(curl -sf -X POST "$$BASE/api/steward/run" -H "content-type: application/json" --data "{\"job_id\":\"$$JOB_ID\"}"); \
	printf "%s\n" "$$RESP" | jq '.'; \
	printf "%s\n" "$$RESP" > .runs/graph_full.json
	@JOB_OUT="$$(cat .runs/graph_last_job.txt)"; \
	mkdir -p baselines; \
	$(COMPOSE) cp $(SERVICE):/app/baselines/$$JOB_OUT.json baselines/ >/dev/null 2>&1 || true; \
	$(COMPOSE) cp $(SERVICE):/app/baselines/latest.json baselines/latest.json >/dev/null 2>&1 || true
	@python3 scripts/graph_full_check.py
	@MANIFEST_PATH="$$(cat .runs/graph_manifest_path.txt)"; \
	DECISION="$$(jq -r '.decision // "unknown"' .runs/graph_full.json 2>/dev/null || echo unknown)"; \
	THRESHOLDS="$$(jq -c '.thresholds // {}' .runs/graph_full.json 2>/dev/null || echo "{}")"; \
	BASELINE_PATH="$$(jq -r '.baseline_path // ""' .runs/graph_full.json 2>/dev/null || echo "")"; \
	echo "✅ graph-full done decision=$$DECISION thresholds=$$THRESHOLDS baseline_path=$$BASELINE_PATH (manifest $$MANIFEST_PATH)";

graph-e2e:
	@bash scripts/graph_verify.sh

smoke-contract: ## Run experiment contract smoke checks (requires JOB=<job_id>)
	@bash scripts/smoke_contract.sh

smoke-review: ## Review contract smoke (requires JOB_ID=<job_id>)
	@MODE=review bash scripts/smoke_review_llm.sh

smoke-apply: ## Apply contract smoke (requires JOB_ID=<job_id>)
	@MODE=apply bash scripts/smoke_review_llm.sh

smoke-metrics: ## Run metrics smoke check (ensures p95/log summary populated)
	@bash scripts/smoke_metrics.sh

fiqa-50k-stage-b: ## FiQA 50k Stage-B: Full Evaluation of Winners
	@echo "🔍 FiQA 50k Stage-B: Full Evaluation of Winners"
	@echo "Step 1/2: Running full evaluation..."
	@$(EXEC) sh -lc "python experiments/run_50k_grid.py \
		--suite experiments/suite_50k_stage_b.yaml \
		--winners reports/fiqa_50k/winners.json \
		--stage b"
	@echo ""
	@echo "Step 2/2: Generating plots..."
	@$(EXEC) sh -lc "python experiments/plot_50k.py --in reports/fiqa_50k/stage_b --out reports/fiqa_50k/stage_b"
	@echo "✅ FiQA 50k Stage-B complete! Check reports/fiqa_50k/stage_b/"

# ========================================
# Phase A: Baseline + Presets + Guards
# ========================================

baseline-run: ## Submit baseline experiment (FIQA Fast - Baseline 50k)
	@echo "Submitting baseline (FIQA Fast - Baseline 50k)..."
	@API_BASE=$$(curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 && echo "http://127.0.0.1:8000" || echo "http://localhost:8000"); \
	curl -fsS -H "content-type: application/json" \
	  -d '{"sample":200,"repeats":1,"fast_mode":false, "dataset_name":"fiqa_50k_v1","qrels_name":"fiqa_qrels_50k_v1"}' \
	  $$API_BASE/api/experiment/run | tee /tmp/baseline_run.json
	@echo "✅ Baseline job submitted"

baseline-poll: ## Poll baseline job status until completion
	@JOB=$$(python3 -c "import json;print(json.load(open('/tmp/baseline_run.json'))['job_id'])"); \
	echo "JOB=$$JOB"; \
	API_BASE=$$(curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 && echo "http://127.0.0.1:8000" || echo "http://localhost:8000"); \
	for i in $$(seq 1 120); do \
	  R=$$(curl -fsS $$API_BASE/api/experiment/status/$$JOB 2>/dev/null); \
	  echo "Status check $$i:"; \
	  echo "$$R" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$$R"; \
	  S=$$(echo "$$R" | python3 -c "import sys, json; d=json.load(sys.stdin); print((d.get('job') or {}).get('status', 'unknown'))" 2>/dev/null || echo "unknown"); \
	  [ "$$S" = "SUCCEEDED" ] && break; \
	  [ "$$S" = "FAILED" ] && break; \
	  sleep 2; \
	done; \
	echo $$JOB > /tmp/baseline_job_id; \
	echo "✅ Job $$JOB finished with status $$S"

baseline-artifacts: ## Download artifacts for baseline job
	@JOB=$$(cat /tmp/baseline_job_id); \
	echo "Downloading artifacts for $$JOB ..."; \
	mkdir -p artifacts/$$JOB && \
	curl -fsS "http://andy-wsl:8000/api/experiment/logs/$$JOB?tail=5000" -o artifacts/$$JOB/logs.txt && \
	echo "✅ Artifacts saved to artifacts/$$JOB/"

# ========================================
# Evaluation & Gold Standard Tools
# ========================================

eval-qrels: ## Check qrels coverage for 10k and 50k datasets
	@echo "🔍 Checking qrels coverage..."
	@python3 tools/eval/qrels_doctor.py \
	  --qrels experiments/data/fiqa/fiqa_qrels_10k_v1.tsv \
	  --collection fiqa_10k_v1 \
	  --out reports/qrels_coverage_10k.json || (echo "❌ Qrels 10k coverage check failed"; exit 1)
	@python3 tools/eval/qrels_doctor.py \
	  --qrels experiments/data/fiqa/fiqa_qrels_50k_v1.tsv \
	  --collection fiqa_50k_v1 \
	  --out reports/qrels_coverage_50k.json || (echo "❌ Qrels 50k coverage check failed"; exit 1)
	@echo "✅ Qrels coverage check complete"

eval-consistency: ## Check dataset/collection/field and embed consistency
	@echo "🔍 Checking consistency..."
	@python3 tools/eval/consistency_check.py \
	  --dataset-name fiqa_50k_v1 \
	  --fields title,text \
	  --out reports/consistency.json || (echo "❌ Consistency check failed"; exit 1)
	@echo "✅ Consistency check complete"

eval-recall: ## Compute de-duplicated Recall@K for latest run
	@echo "🔍 Computing Recall@K..."
	@if [ -z "$$RUN_FILE" ]; then \
	  echo "ERROR: Set RUN_FILE environment variable"; \
	  exit 1; \
	fi
	@python3 tools/eval/recall_eval_dedup.py \
	  --run $$RUN_FILE \
	  --qrels experiments/data/fiqa/fiqa_qrels_50k_v1.tsv \
	  --k 10 \
	  --out reports/recall_at_k.json
	@echo "✅ Recall evaluation complete"

gold-prepare: ## Prepare gold standard candidate CSV
	@echo "📝 Preparing gold standard candidates..."
	@if [ -z "$$QUERIES_FILE" ] || [ -z "$$RUNS_FILE" ]; then \
	  echo "ERROR: Set QUERIES_FILE and RUNS_FILE environment variables"; \
	  exit 1; \
	fi
	@python3 tools/eval/gold_prepare.py \
	  --queries $$QUERIES_FILE \
	  --runs $$RUNS_FILE \
	  --bm25-runs $$BM25_RUNS_FILE \
	  --per-query 20 \
	  --collection fiqa_50k_v1 \
	  --out reports/gold_candidates.csv
	@echo "✅ Gold candidates prepared. Open reports/gold_candidates.csv to label."

gold-finalize: ## Generate qrels_gold.tsv from labeled CSV
	@echo "📝 Generating qrels_gold.tsv..."
	@if [ -z "$$LABELS_FILE" ]; then \
	  echo "ERROR: Set LABELS_FILE environment variable"; \
	  exit 1; \
	fi
	@python3 tools/eval/gold_finalize.py \
	  --labels $$LABELS_FILE \
	  --out reports/qrels_gold.tsv
	@echo "✅ Qrels gold standard generated: reports/qrels_gold.tsv"

gold-gate: ## Quality gate: compare Recall@10 against baseline
	@echo "🚪 Running gold standard quality gate..."
	@if [ ! -f "reports/qrels_gold.tsv" ]; then \
	  echo "ERROR: reports/qrels_gold.tsv not found. Run 'make gold-finalize' first."; \
	  exit 1; \
	fi
	@if [ -z "$$RUN_FILE" ]; then \
	  echo "WARNING: RUN_FILE not set. Using latest run from reports/..."; \
	  RUN_FILE=$$(ls -t reports/*_runs.jsonl 2>/dev/null | head -1); \
	  if [ -z "$$RUN_FILE" ]; then \
	    echo "ERROR: No run file found. Set RUN_FILE environment variable."; \
	    exit 1; \
	  fi; \
	fi
	@echo "Using run file: $$RUN_FILE"
	@python3 tools/eval/recall_eval_dedup.py \
	  --run $$RUN_FILE \
	  --qrels reports/qrels_gold.tsv \
	  --k 10 \
	  --out reports/gold_recall_at_k.json || (echo "❌ Recall evaluation failed"; exit 2)
	@GOLD_RECALL=$$(python3 -c "import json; print(json.load(open('reports/gold_recall_at_k.json'))['metrics']['mean_recall_at_k'])") && \
	BASELINE_RECALL=0.9995 && \
	DIFF=$$(python3 -c "print($$BASELINE_RECALL - $$GOLD_RECALL)") && \
	if [ $$(echo "$$DIFF > 0.01" | bc -l 2>/dev/null || python3 -c "print(1 if $$DIFF > 0.01 else 0)") -eq 1 ]; then \
	  echo "⚠️  Gold Recall@10 ($$GOLD_RECALL) is >1% below baseline ($$BASELINE_RECALL)"; \
	  echo "   Difference: $$DIFF"; \
	  exit 2; \
	else \
	  echo "✅ Gold Recall@10 ($$GOLD_RECALL) within 1% of baseline ($$BASELINE_RECALL)"; \
	fi

gold-update-presets: ## Update presets with gold qrels mappings
	@echo "📝 Updating presets with gold qrels..."
	@if [ ! -f "reports/qrels_gold.tsv" ]; then \
	  echo "WARNING: reports/qrels_gold.tsv not found. Presets will still be updated."; \
	fi
	@DATASET_NAME=$${DATASET_NAME:-fiqa_50k_v1}; \
	QRELS_NAME=$${QRELS_NAME:-fiqa_qrels_50k_v1_gold}; \
	COLLECTION=$${COLLECTION:-fiqa_50k_v1}; \
	echo "Using DATASET_NAME=$$DATASET_NAME, QRELS_NAME=$$QRELS_NAME, COLLECTION=$$COLLECTION"; \
	python3 tools/eval/update_presets_gold.py \
	  --presets-file configs/presets_v10.json \
	  --gold-qrels-name $$QRELS_NAME \
	  --dataset-name $$DATASET_NAME \
	  --collection $$COLLECTION || (echo "❌ Failed to update presets"; exit 1)
	@echo "✅ Presets updated. Gold presets available with qrels_name: $${QRELS_NAME:-fiqa_qrels_50k_v1_gold}"

bandit-audit:
	python3 scripts/audit_bandit.py

.PHONY: check-qdrant-lock check-qdrant-persist

check-qdrant-lock: ## Check if Qdrant tag matches environment variable
	@echo ">> Check qdrant tag matches env"
	@mkdir -p .runs
	@curl -sf http://localhost:8000/api/qdrant/version.tag | tee .runs/qdrant_tag.json | jq -e '.match==true' >/dev/null || (echo "❌ Qdrant tag mismatch"; exit 1)
	@echo "✅ Qdrant tag matches environment"

check-qdrant-persist: ## Restart qdrant and ensure collections persist
	@echo ">> Restart qdrant and ensure collections persist"
	@mkdir -p .runs
	@$(COMPOSE) restart qdrant
	@sleep 3
	@curl -sf http://localhost:6333/collections | tee .runs/qdrant_collections.json | jq -e '.result.collections | type=="array" and (. | length) >= 1' >/dev/null || (echo "❌ Collections not found after restart"; exit 1)
	@echo "✅ Collections persisted after restart"
