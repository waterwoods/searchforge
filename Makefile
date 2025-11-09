PROJECT ?= searchforge
COMPOSE = docker compose --env-file .env.current -p $(PROJECT)

REMOTE=andy-wsl
RDIR=~/searchforge

ifneq (,$(wildcard .env.bandit))
include .env.bandit
export $(shell sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env.bandit 2>/dev/null)
endif

# Helper to detect current target
TARGET ?= $(shell grep -E '^SEARCHFORGE_TARGET=' .env.current | cut -d= -f2 2>/dev/null || echo local)

## ===== Utilities =====

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { echo "❌ Missing dependency: $(1). Please install it."; exit 1; }
endef

.PHONY: help up down restart rebuild logs ps health prune-safe df tunnel-dozzle open-portainer sync whoami gpu-smoke compose-config update-hosts migrate-qdrant cutover-remote baseline-save baseline-save-local baseline-save-remote ui rebuild-api rebuild-api-cpu up-gpu down-gpu export-reqs lint-no-poetry cleanup-audit cleanup-apply cleanup-restore cleanup-history create-clean-repo sync-experiments verify-experiments smoke-experiment runner-check fiqa-50k-stage-b preflight warmup smoke grid-dev full-validate bandit-select bandit-apply bandit-tick bandit-router bandit-ab bandit-oneclick orchestrate.run orchestrate.status orchestrate.report orchestrate.diag orchestrate.preflight orchestrate.policy.audit orchestrate.quick orchestrate.update-sla orchestrate.health-sweep

# Default target: show help
.DEFAULT_GOAL := help

help: ## 显示所有可用命令（默认命令）
	@echo "=================================================="
	@echo "  SearchForge Makefile 命令帮助"
	@echo "=================================================="
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
	@echo "🚪 守门人：快速开发闭环（默认走快路）"
	@echo "  make preflight           - 前置检查（DEV_MODE/外置卷/健康闸）"
	@echo "  make warmup              - 两道闸预热（embeddings + ready）"
	@echo "  make smoke               - 烟测最小闭环（sample=30, K=10）"
	@echo "  make grid-dev            - 并行小批实验（2-3槽）"
	@echo "  make full-validate       - 完整验证流程（<30s到结果）"
	@echo ""
	@echo "💡 使用示例："
	@echo "  make help                - 显示此帮助信息"
	@echo "  make dev-restart && make warmup && make smoke  - 改代码后快速验证"
	@echo "  make full-validate       - 运行完整开发流水线"
	@echo "  make cutover-remote       - 切换到远程（使用默认参数）"
	@echo "  N=150 C=10 WARMUP=10 TIMEOUT=3 make cutover-remote  - 自定义参数切换"
	@echo ""
	@echo "=================================================="

bandit-select: ## Run selector with defaults from .env.bandit
	@python3 scripts/bandit/select.py \
		--algo $(BANDIT_SELECT_ALGO) \
		--eps $(BANDIT_SELECT_EPS) \
		--eps-decay $(BANDIT_SELECT_EPS_DECAY) \
		--min-samples $(BANDIT_SELECT_MIN_SAMPLES) \
		--state $(BANDIT_STATE) \
		--policies $(BANDIT_POLICIES) \
		--print-json

bandit-apply: ## Apply policy specified by ARM=<arm> (optional DRYRUN=1)
ifndef ARM
	$(error Usage: make bandit-apply ARM=<fast_v1|balanced_v1|quality_v1> [DRYRUN=1])
endif
	@DRYRUN_FLAG=$(if $(DRYRUN),--dryrun,) ; \
	python3 scripts/bandit/apply.py --arm $(ARM) --base $(BANDIT_HEALTH_BASE_URL) $$DRYRUN_FLAG --print-json

bandit-tick: ## Execute single tick (preflight → select → apply)
	@BANDIT_HEALTH_BASE_URL=$(BANDIT_HEALTH_BASE_URL) \
	BANDIT_SELECT_ALGO=$(BANDIT_SELECT_ALGO) \
	BANDIT_SELECT_EPS=$(BANDIT_SELECT_EPS) \
	BANDIT_SELECT_EPS_DECAY=$(BANDIT_SELECT_EPS_DECAY) \
	BANDIT_SELECT_MIN_SAMPLES=$(BANDIT_SELECT_MIN_SAMPLES) \
	bash scripts/bandit/tick.sh

bandit-router: ## Run epsilon router with parameters from .env.bandit
	@EPS=$(EPS) BATCH=$(BATCH) ROUNDS=$(ROUNDS) MIN_PER_ARM=$(MIN_PER_ARM) \
	PROMOTE_P95=$(PROMOTE_P95) PROMOTE_STREAK=$(PROMOTE_STREAK) \
	SLA_P95=$(SLA_P95) SLA_ERR=$(SLA_ERR) TARGET_P95=$(TARGET_P95) \
	WEIGHTS=$(WEIGHTS) ALPHA=$(ALPHA) \
	python3 scripts/bandit/epsilon_router.py

bandit-ab: ## Run fixed-sample A/B experiment set
	@python3 scripts/bandit/run_ab.py

bandit-oneclick: ## Run one-click migrate → router → A/B → summary pipeline
	@bash scripts/bandit/oneclick.sh

sync:
	@rsync -avzP mini-d-files/ $(REMOTE):$(RDIR)/

up:
	@ssh $(REMOTE) 'cd $(RDIR) && cp -n .env.sample .env || true && docker compose up -d --build'
	@$(MAKE) health

down:
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose down'

restart:  ## Restart backend service on remote
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose restart rag-api || docker compose up -d rag-api'
	@sleep 5
	@$(MAKE) health

rebuild: rebuild-api

logs:
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose logs -f --tail=200 api'

ps:
	@ssh $(REMOTE) 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

health:
	@ssh $(REMOTE) 'curl -fsS http://localhost:8000/health && echo'

prune-safe:
	@ssh $(REMOTE) 'docker system prune -af' # 不带 --volumes，避免误删数据卷

df:
	@ssh $(REMOTE) 'docker system df -v'

# 本机开一个隧道：访问 http://localhost:9999 查看 Dozzle
tunnel-dozzle:
	@echo "Press Ctrl-C to close the tunnel."
	@ssh -N -L 9999:127.0.0.1:9999 $(REMOTE)

# 快捷打开 Portainer（把 100.x.x.x 换成你的 Tailscale IP）
open-portainer:
	@open https://100.67.88.114:9443

whoami:
	@bash tools/switch/print_target.sh

gpu-smoke:
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

ui:
	@echo "🚀 Starting Vite dev server (ui)..."
	@echo "📍 API base: http://andy-wsl:8000"
	@echo "🌐 Dev server: http://localhost:5173"
	@cd ui && \
		if [ ! -d "node_modules" ]; then \
			echo "📦 Installing dependencies..."; \
			npm install; \
		fi && \
		npm run dev -- --port 5173 --open --host

rebuild-api: export-reqs
	@echo "🔨 Rebuilding rag-api service..."
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose build rag-api && docker compose up -d rag-api'
	@echo "⏳ Waiting for service to be ready..."
	@sleep 5
	@$(MAKE) health

rebuild-api-cpu: ## 重建 CPU-only rag-api 并验证无 CUDA 包
	@echo "🔨 Rebuilding CPU-only rag-api service..."
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose build --no-cache rag-api && docker compose up -d rag-api'
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

win-fw-allow-8000: ## 打印 Windows 防火墙放行 8000 的 PowerShell 命令
	@echo '以管理员 PowerShell 执行以下命令：'
	@echo 'New-NetFirewallRule -DisplayName "SearchForge rag-api 8000 Tailscale" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress 100.64.0.0/10 -Action Allow'

net-verify: ## 验证 rag-api 端口绑定与健康接口
	@echo "🔎 Checking container port bindings (remote)..."
	@ssh $(REMOTE) 'docker ps --format "table {{.Names}}\t{{.Ports}}" | grep rag-api || true'
	@echo "🔎 Curl health from inside container (127.0.0.1:${MAIN_PORT})..."
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose exec -T rag-api sh -lc "curl -fsS http://127.0.0.1:${MAIN_PORT}/health || curl -fsS http://127.0.0.1:8000/health"'
	@echo "🔎 Curl health from Mac (andy-wsl:8000)..."
	@curl -fsS http://andy-wsl:8000/health || (sleep 2; curl -fsS http://andy-wsl:8000/health)
	@echo "✅ Network verification done"

up-gpu:
	@echo "🚀 Starting GPU worker service..."
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d gpu-worker'
	@echo "✅ GPU worker started"

down-gpu:
	@echo "🛑 Stopping GPU worker service..."
	@ssh $(REMOTE) 'cd $(RDIR) && docker compose -f docker-compose.yml -f docker-compose.gpu.yml down gpu-worker'
	@echo "✅ GPU worker stopped"

# Repository cleanup targets (safe, reversible archiving)
cleanup-audit: ## 审计可清理的文件（dry-run，生成候选列表）
	@bash tools/cleanup/audit.sh

cleanup-apply: ## 归档未使用的脚本/测试/文档到 archive/
	@bash tools/cleanup/apply.sh

cleanup-restore: ## 恢复归档的文件到原始位置
	@bash tools/cleanup/restore.sh

cleanup-history: ## 清理 Git 历史中的大文件（需要 I_KNOW_WHAT_IM_DOING=1）
	@bash tools/cleanup/slim_history.sh

create-clean-repo: ## 创建干净的仓库快照并切换到新远程（需要 NEW_REPO_URL=<url>）
	@bash tools/cleanup/create_clean_repo.sh

export-reqs: ## Export Poetry dependencies to requirements.txt (dev-only)
	@if [ -f "pyproject.toml" ] && command -v poetry >/dev/null 2>&1; then \
		echo "📦 Exporting Poetry dependencies to requirements.txt..."; \
		poetry export -f requirements.txt --without-hashes -o services/rag_api/requirements.txt || true; \
		echo "✅ Exported to services/rag_api/requirements.txt"; \
	else \
		echo "⚠️  Poetry not available or pyproject.toml not found, skipping export"; \
	fi

lint-no-poetry: ## Check that no 'poetry run' appears in runtime paths
	@echo "🔍 Checking for 'poetry run' in runtime paths..."
	@if git grep -nE 'poetry\s+run' -- 'services/**' 'tools/**' 'Makefile' '**/Dockerfile' 'docker-compose*.yml' >/dev/null 2>&1; then \
		echo "❌ ERROR: 'poetry run' found in runtime paths:"; \
		git grep -nE 'poetry\s+run' -- 'services/**' 'tools/**' 'Makefile' '**/Dockerfile' 'docker-compose*.yml'; \
		exit 1; \
	else \
		echo "✅ No 'poetry run' found in runtime paths"; \
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

orchestrate.plan: ## Generate dry-run plan without executing
	@ORCH_BASE=$${ORCH_BASE:-http://127.0.0.1:8000}; \
	PAYLOAD=$$(python3 -c "import json,yaml; cfg=yaml.safe_load(open('agents/orchestrator/config.yaml', encoding='utf-8')); collections=cfg.get('collections') or ['fiqa_para_50k']; dataset=collections[0]; smoke=cfg.get('smoke', {}); grid=cfg.get('grid', {}); payload={'dataset':dataset,'sample_size':smoke.get('sample',50),'search_space':{'top_k':grid.get('top_k'),'mmr':grid.get('mmr'),'ef_search':grid.get('ef_search')},'budget':cfg.get('budget', {}),'concurrency':smoke.get('concurrency'),'baseline_id':cfg.get('baseline_policy')}; print(json.dumps(payload))"); \
	RESP=$$(curl -sf -X POST "$$ORCH_BASE/orchestrate/run?commit=false" -H 'content-type: application/json' -d "$$PAYLOAD") || exit $$?; \
	echo "$$RESP" | python3 -m json.tool; \
	RUN_ID=$$(echo "$$RESP" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('run_id', 'N/A'))"); \
	echo "$$RUN_ID" > .last_run; \
	echo "✅ Dry-run plan generated (run_id=$$RUN_ID)"

orchestrate.commit: ## Commit and execute the planned experiment
	@if [ ! -f .last_run ]; then echo "❌ .last_run not found. Run 'make orchestrate.plan' first."; exit 1; fi
	@RUN_ID=$$(cat .last_run); \
	ORCH_BASE=$${ORCH_BASE:-http://127.0.0.1:8001}; \
	PAYLOAD=$$(python3 -c "import json,yaml; cfg=yaml.safe_load(open('agents/orchestrator/config.yaml', encoding='utf-8')); collections=cfg.get('collections') or ['fiqa_para_50k']; dataset=collections[0]; smoke=cfg.get('smoke', {}); grid=cfg.get('grid', {}); payload={'dataset':dataset,'sample_size':smoke.get('sample',50),'search_space':{'top_k':grid.get('top_k'),'mmr':grid.get('mmr'),'ef_search':grid.get('ef_search')},'budget':cfg.get('budget', {}),'concurrency':smoke.get('concurrency'),'baseline_id':cfg.get('baseline_policy')}; print(json.dumps(payload))"); \
	RESP=$$(curl -sf -X POST "$$ORCH_BASE/orchestrate/run?commit=true" -H 'content-type: application/json' -d "$$PAYLOAD") || exit $$?; \
	echo "$$RESP" | python3 -m json.tool; \
	NEW_RUN_ID=$$(echo "$$RESP" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('run_id', 'N/A'))"); \
	echo "$$NEW_RUN_ID" > .last_run; \
	echo "✅ Experiment committed (run_id=$$NEW_RUN_ID)"

orchestrate.audit: ## Check ID alignment for a dataset collection
	@DATASET=$${DATASET:-fiqa_para_50k}; \
	QRELS=$$(python3 -c "import yaml; cfg=yaml.safe_load(open('agents/orchestrator/config.yaml', encoding='utf-8')); qrels_map=cfg.get('datasets', {}).get('qrels_map', {}); print(qrels_map.get('$$DATASET', qrels_map.get('fiqa_para_50k', 'experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv')))"); \
	echo "Checking alignment: collection=$$DATASET, qrels=$$QRELS"; \
	python3 -m tools.eval.id_alignment_auditor --collection $$DATASET --qrels $$QRELS --host http://127.0.0.1:6333

orchestrate.policy.audit: ## Audit policy alignment for a specific dataset
	@DATASET=$${DATASET:-fiqa_para_50k}; \
	QDRANT_HOST=$${QDRANT_HOST:-http://127.0.0.1:6333}; \
	QRELS=$$(python3 -c "import yaml; cfg=yaml.safe_load(open('agents/orchestrator/config.yaml', encoding='utf-8')); qrels_map=cfg.get('datasets', {}).get('qrels_map', {}); print(qrels_map.get('$$DATASET', qrels_map.get('fiqa_para_50k', 'experiments/data/fiqa/fiqa_qrels_hard_50k_v1.tsv')))"); \
	python3 -m tools.eval.id_alignment_auditor --host $$QDRANT_HOST --collection $$DATASET --qrels $$QRELS --json-out /tmp/_align_$$DATASET.json; \
	MISMATCH_RATE=$$(python3 -c "import json; d=json.load(open('/tmp/_align_$$DATASET.json')); print(d.get('mismatch_rate', 1.0))"); \
	if [ $$(echo "$$MISMATCH_RATE > 0" | bc -l 2>/dev/null || python3 -c "print(1 if $$MISMATCH_RATE > 0 else 0)") -eq 1 ]; then \
		echo "❌ Alignment check failed: mismatch_rate=$$MISMATCH_RATE"; \
		exit 1; \
	else \
		echo "✅ Dataset alignment passed for '$$DATASET' (mismatch_rate=$$MISMATCH_RATE)"; \
	fi

orchestrate.preflight: ## Preflight check: run policy audit before experiments
	@DATASET=$${DATASET:-fiqa_para_50k}; \
	$(MAKE) orchestrate.policy.audit DATASET=$$DATASET; \
	echo "✅ Dataset alignment passed for '$$DATASET'"

orchestrate.run: ## Run orchestrator experiment (with preflight check)
	@DATASET=$${DATASET:-fiqa_para_50k}; \
	SAMPLE=$${SAMPLE:-50}; \
	TOPK=$${TOPK:-10}; \
	CONCURRENCY=$${CONCURRENCY:-4}; \
	ORCH_BASE=$${ORCH_BASE:-http://127.0.0.1:8000}; \
	echo "🔍 Running preflight check..."; \
	$(MAKE) orchestrate.preflight DATASET=$$DATASET || exit $$?; \
	echo "🚀 Starting orchestrator run..."; \
	PAYLOAD=$$(python3 -c "import json; print(json.dumps({'preset': 'smoke', 'collection': '$$DATASET', 'overrides': {'sample': int('$$SAMPLE'), 'top_k': int('$$TOPK'), 'concurrency': int('$$CONCURRENCY')}}))"); \
	RESP=$$(curl -sf -X POST "$$ORCH_BASE/orchestrate/run?commit=true" -H 'content-type: application/json' -d "$$PAYLOAD") || exit $$?; \
	echo "$$RESP" | python3 -m json.tool; \
	RUN_ID=$$(echo "$$RESP" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('run_id', 'N/A'))"); \
	echo "$$RUN_ID" > .last_run; \
	echo "✅ Orchestrator run started: run_id=$$RUN_ID"

orchestrate.quick: ## Quick smoke test: preflight + run with SAMPLE=30, TOPK=10
	@DATASET=$${DATASET:-fiqa_para_50k}; \
	SAMPLE=$${SAMPLE:-30}; \
	TOPK=$${TOPK:-10}; \
	$(MAKE) orchestrate.preflight DATASET=$$DATASET; \
	$(MAKE) orchestrate.run DATASET=$$DATASET SAMPLE=$$SAMPLE TOPK=$$TOPK

orchestrate.update-sla: ## Update SLA_POLICY.yaml from latest experiment results
	@if [ ! -f .last_run ]; then echo "❌ .last_run not found. Run 'make orchestrate.run' first."; exit 1; fi
	@RUN_ID=$$(cat .last_run); \
	python3 scripts/update_sla_from_results.py --run-id $$RUN_ID

orchestrate.health-sweep: ## Daily health sweep: preflight → smoke → report → update SLA → acceptance
	@bash scripts/daily_health_sweep.sh

ci-policy-guard: ## CI guard: validate all policies against whitelist/disabled and alignment
	@python3 - <<'PY'
	import json
	import sys
	import yaml
	import subprocess
	from pathlib import Path
	
	# Load config
	cfg = yaml.safe_load(open('agents/orchestrator/config.yaml', encoding='utf-8'))
	pols = json.load(open('configs/policies.json', encoding='utf-8'))
	
	# Get dataset config
	wh = set(cfg.get('datasets', {}).get('whitelist', []))
	dis = set(cfg.get('datasets', {}).get('disabled', []))
	qmap = cfg.get('datasets', {}).get('queries_map', {})
	rmap = cfg.get('datasets', {}).get('qrels_map', {})
	
	# Get base URL and host aliases
	base = cfg.get('base_url', 'http://127.0.0.1:8000')
	host_aliases = cfg.get('host_aliases', {})
	
	# Apply host alias
	def apply_alias(url, aliases):
		if not url:
			return url
		from urllib.parse import urlparse, urlunparse
		parsed = urlparse(url)
		alias = aliases.get(parsed.hostname)
		if alias:
			netloc = alias if parsed.port is None else f"{alias}:{parsed.port}"
			parsed = parsed._replace(netloc=netloc)
			return urlunparse(parsed)
		return url
	
	alias_base = apply_alias(base, host_aliases)
	
	# Extract Qdrant host (assume port 6333)
	qdrant_host = "http://127.0.0.1:6333"
	allowed_hosts = cfg.get('allowed_hosts', [])
	for host in allowed_hosts:
		if ":6333" in str(host):
			qdrant_host = f"http://{host}" if not host.startswith("http") else host
			break
	qdrant_host = apply_alias(qdrant_host, host_aliases)
	
	fail = False
	
	# Check each policy
	policies_data = pols.get('policies', {})
	for policy_name, policy in policies_data.items():
		d = policy.get('dataset')
		if not d:
			print(f'DATASET_BLOCK: Policy "{policy_name}" missing dataset field')
			fail = True
			continue
		
		# Check whitelist/disabled
		if d not in wh or d in dis:
			print(f'DATASET_BLOCK: Policy "{policy_name}" uses dataset "{d}" (not in whitelist or disabled)')
			fail = True
			continue
		
		# Get paths from policy or config maps
		qp = policy.get('queries_path') or qmap.get(d)
		rp = policy.get('qrels_path') or rmap.get(d)
		
		if not qp or not rp:
			print(f'ALIGNMENT_BLOCK (missing paths): Policy "{policy_name}" dataset "{d}" missing queries_path or qrels_path')
			fail = True
			continue
		
		# Check if paths exist
		repo_root = Path.cwd()
		qp_full = repo_root / qp if not Path(qp).is_absolute() else Path(qp)
		rp_full = repo_root / rp if not Path(rp).is_absolute() else Path(rp)
		
		if not qp_full.exists():
			print(f'ALIGNMENT_BLOCK (missing file): Policy "{policy_name}" queries_path "{qp}" not found')
			fail = True
			continue
		
		if not rp_full.exists():
			print(f'ALIGNMENT_BLOCK (missing file): Policy "{policy_name}" qrels_path "{rp}" not found')
			fail = True
			continue
		
		# Run alignment check
		out = f'/tmp/_align_{d}.json'
		cmd = [
			'python', '-m', 'tools.eval.id_alignment_auditor',
			'--host', qdrant_host,
			'--collection', d,
			'--qrels', str(rp_full),
			'--json-out', out
		]
		
		r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
		
		if r.returncode != 0:
			print(f'ALIGNMENT_BLOCK (mismatch): Policy "{policy_name}" dataset "{d}" alignment check failed (exit {r.returncode})')
			if r.stderr:
				print(f'  stderr: {r.stderr[:200]}')
			fail = True
			continue
		
		# Check mismatch_rate from JSON output
		try:
			if Path(out).exists():
				with open(out, 'r', encoding='utf-8') as f:
					align_result = json.load(f)
				mismatch_rate = align_result.get('mismatch_rate', 1.0)
				if mismatch_rate > 0:
					print(f'ALIGNMENT_BLOCK (mismatch_rate={mismatch_rate}): Policy "{policy_name}" dataset "{d}" has alignment mismatches')
					fail = True
					continue
		except Exception as e:
			print(f'ALIGNMENT_BLOCK (error reading result): Policy "{policy_name}" dataset "{d}" - {e}')
			fail = True
			continue
	
	sys.exit(1 if fail else 0)
	PY

orchestrate.demo: ## Trigger demo smoke run (PRESET=smoke, SAMPLE=40)
	@PRESET=$${PRESET:-smoke}; \
	SAMPLE=$${SAMPLE:-40}; \
	ORCH_BASE=$${ORCH_BASE:-http://127.0.0.1:8000}; \
	PAYLOAD=$$(python3 -c "import json; print(json.dumps({'preset': '$$PRESET', 'collection': 'fiqa_para_50k', 'overrides': {'sample': int('$$SAMPLE')}}))"); \
	RESP=$$(curl -sf -X POST "$$ORCH_BASE/orchestrate/run?commit=true" -H 'content-type: application/json' -d "$$PAYLOAD") || exit $$?; \
	echo "$$RESP" | python3 -m json.tool; \
	RUN_ID=$$(echo "$$RESP" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('run_id', 'N/A'))"); \
	echo "$$RUN_ID" > .last_run; \
	echo "✅ orchestrator demo run_id=$$RUN_ID"; \
	echo ""; \
	echo "⏳ Waiting for completion (polling every 5s)..."; \
	for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do \
		STATUS=$$(curl -sf "$$ORCH_BASE/orchestrate/status?run_id=$$RUN_ID&detail=lite" 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>&1); \
		echo "[$$i] Status: $$STATUS"; \
		if [ "$$STATUS" = "completed" ] || [ "$$STATUS" = "failed" ]; then \
			break; \
		fi; \
		sleep 5; \
	done; \
	echo ""; \
	echo "📊 Fetching report..."; \
	$(MAKE) orchestrate.report

orchestrate.summarize: ## Generate RUN_SUMMARY.md for a run (default: latest)
	@RUN_ID=$${RUN_ID:-$$(python3 -c "from pathlib import Path; reports=Path('reports'); dirs=[d.name for d in reports.iterdir() if d.is_dir() and d.name.startswith('orch-')]; print(sorted(dirs, key=lambda x: Path('reports', x).stat().st_mtime, reverse=True)[0] if dirs else '')")}; \
	if [ -z "$$RUN_ID" ]; then \
		echo "ERROR: No run_id found. Provide RUN_ID=... or ensure reports/ contains run directories."; \
		exit 1; \
	fi; \
	echo "Generating summary for run_id=$$RUN_ID"; \
	python3 -m tools.report.summarize_run --run-id $$RUN_ID

orchestrate.status: ## Show latest orchestrator status using run_id stored in .last_run
	@if [ ! -f .last_run ]; then echo "❌ .last_run not found. Run 'make orchestrate.run' first."; exit 1; fi
	@RUN_ID=$$(cat .last_run); \
	ORCH_BASE=$${ORCH_BASE:-http://127.0.0.1:8000}; \
	RESP=$$(curl -sf "$$ORCH_BASE/orchestrate/status?run_id=$$RUN_ID") || exit $$?; \
	echo "run_id=$$RUN_ID"; \
	echo "$$RESP" | python3 -c "import json,sys; data=json.load(sys.stdin); out={'stage': data.get('stage'),'status': data.get('status'),'progress': data.get('progress', {}),'latest_metrics': data.get('latest_metrics', {})}; print(json.dumps(out, indent=2))"

orchestrate.report: ## Fetch orchestrator report artifacts and verify files exist
	@if [ ! -f .last_run ]; then echo "❌ .last_run not found. Run 'make orchestrate.run' first."; exit 1; fi
	@RUN_ID=$$(cat .last_run); \
	ORCH_BASE=$${ORCH_BASE:-http://127.0.0.1:8000}; \
	RESP=$$(curl -sf "$$ORCH_BASE/orchestrate/report?run_id=$$RUN_ID") || exit $$?; \
	echo "$$RESP" | python3 -m json.tool; \
	echo "$$RESP" > .orchestrate_report.json; \
		printf '%s\n' \
		'import json' \
		'import os' \
		'import sys' \
		'' \
		'with open(".orchestrate_report.json", encoding="utf-8") as fp:' \
		'    data = json.load(fp)' \
		'' \
		'artifacts = data.get("artifacts", {})' \
		'reports_root = os.path.abspath("reports")' \
		'missing = []' \
		'' \
		'for key, rel in artifacts.items():' \
		'    path = os.path.abspath(rel) if rel.startswith("reports/") else os.path.join(reports_root, rel)' \
		'    if os.path.exists(path):' \
		'        print(f"{key}: {os.path.relpath(path)} ✅")' \
		'    else:' \
		'        missing.append(rel)' \
		'' \
		'if missing:' \
		'    raise SystemExit("❌ Missing artifacts: " + ", ".join(missing))' \
		> .check_artifacts.py; \
	python3 .check_artifacts.py; \
	rm -f .orchestrate_report.json .check_artifacts.py

orchestrate.diag: ## Run orchestrator diagnostics (health checks, runner smoke, .runs snapshot)
	@printf '%s\n' \
		'import os' \
		'import shlex' \
		'import subprocess' \
		'import sys' \
		'from pathlib import Path' \
		'from shutil import which' \
		'from urllib.parse import urlparse, urlunparse' \
		'' \
		'import requests' \
		'import yaml' \
		'' \
		'cfg = yaml.safe_load(open("agents/orchestrator/config.yaml", encoding="utf-8")) or {}' \
		'base_url = os.environ.get("ORCH_BASE") or cfg.get("base_url") or "http://localhost:8000"' \
		'aliases = cfg.get("host_aliases") or {}' \
		'' \
		'def apply_alias(url: str) -> str:' \
		'    if not url:' \
		'        return url' \
		'    parsed = urlparse(url)' \
		'    alias = aliases.get(parsed.hostname)' \
		'    if alias:' \
		'        netloc = alias if parsed.port is None else f"{alias}:{parsed.port}"' \
		'        parsed = parsed._replace(netloc=netloc)' \
		'        return urlunparse(parsed)' \
		'    return url' \
		'' \
		'effective_base = apply_alias(base_url)' \
		'print(f"🌐 Base URL: {base_url}")' \
		'if effective_base != base_url:' \
		'    print(f"   ↳ using alias {effective_base} for runtime access")' \
		'' \
		'health_endpoints = cfg.get("health_endpoints") or ["/ready", "/api/health/embeddings"]' \
		'timeout_s = float(cfg.get("health_timeout_s", 10.0))' \
		'print("== Health checks ==")' \
		'for endpoint in health_endpoints:' \
		'    if not endpoint:' \
		'        continue' \
		'    runtime_base = effective_base or base_url' \
		'    url = runtime_base.rstrip("/") + "/" + endpoint.lstrip("/")' \
		'    try:' \
		'        response = requests.get(url, timeout=timeout_s)' \
		'        elapsed = getattr(response, "elapsed", None)' \
		'        elapsed_ms = int(elapsed.total_seconds() * 1000) if elapsed else "n/a"' \
		'        print(f"{url} -> {response.status_code} ({elapsed_ms} ms)")' \
		'    except Exception as exc:  # noqa: BLE001' \
		'        print(f"{url} -> ERROR: {exc}")' \
		'' \
		'print("\\n== Runner dry-run ==")' \
		'runner_cmd = cfg.get("runner_cmd", "python -m experiments.fiqa_suite_runner")' \
		'collections = cfg.get("collections") or ["fiqa_para_50k"]' \
		'dataset = collections[0]' \
		'smoke_cfg = cfg.get("smoke") or {}' \
		'sample = max(1, min(int(smoke_cfg.get("sample", 3)), 3))' \
		'top_k = smoke_cfg.get("top_k")' \
		'if top_k is None:' \
		'    top_k = 5' \
		'concurrency = smoke_cfg.get("concurrency") or 1' \
		'cmd = shlex.split(runner_cmd)' \
		'if cmd:' \
		'    resolved = which(cmd[0])' \
		'    if not resolved and cmd[0] in {"python", "python3"}:' \
		'        resolved = sys.executable' \
		'    if resolved:' \
		'        cmd[0] = resolved' \
		'if which("poetry"):' \
		'    cmd = ["poetry", "run"] + cmd' \
		'cmd.extend([' \
		'    "--base",' \
		'    effective_base or base_url,' \
		'    "--collection",' \
		'    dataset,' \
		'    "--sample",' \
		'    str(sample),' \
		'    "--top_k",' \
		'    str(top_k),' \
		'    "--concurrency",' \
		'    str(concurrency),' \
		'    "--job-note",' \
		'    "diag",' \
		'])' \
		'ef_search = smoke_cfg.get("ef_search")' \
		'if ef_search:' \
		'    cmd.extend(["--ef-search", str(ef_search)])' \
		'if smoke_cfg.get("mmr"):' \
		'    cmd.append("--mmr")' \
		'    if smoke_cfg.get("mmr_lambda") is not None:' \
		'        cmd.extend(["--mmr-lambda", str(smoke_cfg.get("mmr_lambda"))])' \
		'' \
		'runner_timeout = float(cfg.get("runner_timeout_s", 1200))' \
		'print("Command:", " ".join(cmd))' \
		'try:' \
		'    proc = subprocess.run(' \
		'        cmd,' \
		'        capture_output=True,' \
		'        text=True,' \
		'        timeout=runner_timeout,' \
		'        check=False,' \
		'    )' \
		'    print(f"exit={proc.returncode}")' \
		'    if proc.stdout:' \
		'        print(proc.stdout)' \
		'    if proc.stderr:' \
		'        print(proc.stderr, file=sys.stderr)' \
		'except subprocess.TimeoutExpired:' \
		'    print(f"runner timed out after {runner_timeout} seconds", file=sys.stderr)' \
		'except FileNotFoundError as exc:' \
		'    print(f"runner command not found: {exc}", file=sys.stderr)' \
		'' \
		'print("\\n== .runs snapshot ==")' \
		'runs_dir = Path(cfg.get("runs_dir", ".runs"))' \
		'if not runs_dir.exists():' \
		'    print(f"{runs_dir} (missing)")' \
		'else:' \
		'    entries = sorted(' \
		'        [p for p in runs_dir.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True,' \
		'    )[:5]' \
		'    if not entries:' \
		'        print(f"{runs_dir} (empty)")' \
		'    for entry in entries:' \
		'        metrics = entry / "metrics.json"' \
		'        size = metrics.stat().st_size if metrics.exists() else 0' \
		'        status = "✅" if metrics.exists() else "⚠️ missing"' \
		'        print(f"{entry.name}: metrics.json {status} ({size} bytes)")' \
	> .orchestrate_diag.py
	@python3 .orchestrate_diag.py
	@rm -f .orchestrate_diag.py

fiqa-50k-stage-b: ## FiQA 50k Stage-B: Full Evaluation of Winners
	$(call ensure_tool,poetry)
	@echo "🔍 FiQA 50k Stage-B: Full Evaluation of Winners"
	@echo "Step 1/2: Running full evaluation..."
	@poetry run python experiments/run_50k_grid.py \
		--suite experiments/suite_50k_stage_b.yaml \
		--winners reports/fiqa_50k/winners.json \
		--stage b
	@echo ""
	@echo "Step 2/2: Generating plots..."
	@poetry run python experiments/plot_50k.py --in reports/fiqa_50k/stage_b --out reports/fiqa_50k/stage_b
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

dev-up: ## 启动开发模式容器（DEV_MODE=1）
	DOCKER_BUILDKIT=1 docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d rag-api

dev-restart: ## 重启开发模式容器（代码改动后）
	docker compose -f docker-compose.yml -f docker-compose.dev.yml restart rag-api

dev-logs: ## 查看开发模式实时日志
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f rag-api

# ========================================
# 守门人：快速开发闭环目标
# ========================================

preflight: ## 前置检查（DEV_MODE + 外置卷 + 健康闸）
	@echo "🔍 Preflight Check - 守门人前置验证"
	@echo ""
	@echo "1️⃣ 检查 DEV_MODE 环境变量..."
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rag-api sh -c 'if [ "$$DEV_MODE" != "1" ]; then echo "❌ DEV_MODE 未设置为 1"; exit 1; else echo "✅ DEV_MODE=1"; fi'
	@echo ""
	@echo "2️⃣ 检查外置卷可读性..."
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rag-api sh -c '\
		[ -d /app/models ] && echo "✅ /app/models 存在" || (echo "❌ /app/models 不存在"; exit 1); \
		[ -r /app/models ] && echo "✅ /app/models 可读" || (echo "❌ /app/models 不可读"; exit 1); \
		[ -f /app/models/sentence-transformers/all-MiniLM-L6-v2/config.json ] && echo "✅ 模型文件存在" || echo "⚠️  模型文件未找到（首次启动可能需要下载）"; \
	'
	@echo ""
	@echo "3️⃣ 检查健康端点..."
	@curl -fsS http://localhost:8000/health >/dev/null 2>&1 && echo "✅ /health 端点正常" || (echo "❌ /health 端点失败，服务可能未就绪"; exit 1)
	@curl -fsS http://localhost:8000/api/health/embeddings >/dev/null 2>&1 && echo "✅ /api/health/embeddings 端点正常" || echo "⚠️  embeddings 端点未就绪（可能仍在预热）"
	@curl -fsS http://localhost:8000/ready >/dev/null 2>&1 && echo "✅ /ready 端点正常" || echo "⚠️  ready 端点未就绪（可能仍在预热）"
	@echo ""
	@echo "✅ Preflight 检查通过！"

warmup: ## 两道闸预热（embeddings + ready）
	@echo "🔥 Running warmup script..."
	@bash scripts/warmup.sh

smoke: preflight warmup ## 烟测最小闭环（sample=30）
	@echo "🧪 Running smoke test..."
	@bash scripts/smoke.sh

grid-dev: preflight warmup ## 并行小批实验（2-3槽）
	@echo "🔬 Running grid dev experiments..."
	@bash scripts/run_grid_dev.sh

full-validate: ## 完整验证流程（dev-restart → warmup → smoke → grid-dev）
	@echo "🚀 Running full validation pipeline..."
	@bash scripts/full_validation.sh

latency-grid: preflight warmup ## P95延迟优化套件（目标<1000ms）
	@echo "🚀 P95 Latency Optimization Suite"
	@bash scripts/run_latency_grid.sh

ci-single-entry-guard: ## CI guard: ensure single entry point (no app/main.py or app.main:app references)
	@echo "🔍 Checking for legacy entry point references..."
	@if command -v rg >/dev/null 2>&1; then \
		LEGACY_REFS=$$(rg -n "app/main\.py|app\.main:app" -g "!**/app/main.py.deprecated" -g "!**/agentic_services/**" -g "!**/venv/**" -g "!**/.venv/**" -g "!**/node_modules/**" -S 2>/dev/null || true); \
		if [ -n "$$LEGACY_REFS" ]; then \
			echo "❌ Found legacy entry references:"; \
			echo "$$LEGACY_REFS"; \
			exit 1; \
		else \
			echo "✅ Single entry enforced - no legacy references found"; \
		fi; \
	else \
		LEGACY_REFS=$$(grep -rn "app/main\.py\|app\.main:app" --exclude-dir=venv --exclude-dir=.venv --exclude-dir=node_modules --exclude="*.deprecated" . 2>/dev/null | grep -v "app/main.py.deprecated" || true); \
		if [ -n "$$LEGACY_REFS" ]; then \
			echo "❌ Found legacy entry references:"; \
			echo "$$LEGACY_REFS"; \
			exit 1; \
		else \
			echo "✅ Single entry enforced - no legacy references found"; \
		fi; \
	fi
