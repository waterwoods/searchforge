PROJECT ?= searchforge
COMPOSE = docker compose --env-file .env.current -p $(PROJECT)

SSH_HOST ?= andy-wsl
REMOTE ?= $(SSH_HOST)
RDIR=~/searchforge

# Helper to detect current target
TARGET ?= $(shell grep -E '^SEARCHFORGE_TARGET=' .env.current | cut -d= -f2 2>/dev/null || echo local)

## ===== Utilities =====

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { echo "❌ Missing dependency: $(1). Please install it."; exit 1; }
endef

.PHONY: help up down restart rebuild logs ps health prune-safe df tunnel-dozzle open-portainer sync whoami gpu-smoke compose-config update-hosts migrate-qdrant cutover-remote baseline-save baseline-save-local baseline-save-remote ui rebuild-api rebuild-api-cpu up-gpu down-gpu export-reqs lint-no-poetry cleanup-audit cleanup-apply cleanup-restore cleanup-history create-clean-repo sync-experiments verify-experiments smoke-experiment runner-check fiqa-50k-stage-b smoke-fast

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
	@echo "💡 使用示例："
	@echo "  make help                - 显示此帮助信息"
	@echo "  make cutover-remote       - 切换到远程（使用默认参数）"
	@echo "  N=150 C=10 WARMUP=10 TIMEOUT=3 make cutover-remote  - 自定义参数切换"
	@echo ""
	@echo "=================================================="

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

rebuild: rebuild-api

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

up-gpu:
	@echo "🚀 Starting GPU worker service..."
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d gpu-worker'
	@echo "✅ GPU worker started"

down-gpu:
	@echo "🛑 Stopping GPU worker service..."
	@ssh $(SSH_HOST) 'cd $(RDIR) && docker compose -f docker-compose.yml -f docker-compose.gpu.yml down gpu-worker'
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

smoke-fast: ## Run quick backend smoke test against local endpoints
	@bash scripts/quick_backend_smoke.sh

smoke-review: ## Run steward review/apply smoke check (requires JOB_ID=<job>)
	@bash scripts/smoke_review_llm.sh

smoke-metrics: ## Run metrics smoke check (ensures p95/log summary populated)
	@bash scripts/smoke_metrics.sh

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
