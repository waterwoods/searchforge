PROJECT=searchforge
REMOTE=andy@100.67.88.114
REMOTE_DIR=~/searchforge

.PHONY: build up down logs health sync abtest pack base

build:
	docker compose build rag-api auto-tuner

up:
\tdocker compose up -d

down:
\tdocker compose down --remove-orphans

logs:
\tdocker compose logs -f --tail=200

health:
\tcurl -fsS http://localhost:8080/health || (echo "health failed" && exit 1)

sync:
\trsync -av --files-from=manifests/manifest.txt --exclude-from=manifests/exclude.txt ./ $(REMOTE):$(REMOTE_DIR)/

abtest:
\tssh $(REMOTE) 'bash -lc "cd $(REMOTE_DIR) && nohup python eval/run_ab_30m_evaluation.py --config eval/configs/evaluation_config.json --output reports --seed 42 --force-full-run > reports/full_run_$(date +%F_%H%M).log 2>&1 &"'

pack:
\ttar czf reports/ab_artifacts_$(shell date +%F_%H%M).tgz reports