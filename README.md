# searchforge
Minimal, production-like RAG infra: probe + shadow + chaos + auto-tuner + AB eval.

## Quickstart
docker compose up -d
docker compose exec rag-api python -c "import torch, sentence_transformers as s;print(torch,torch.__version__,cuda=,torch.version.cuda);print(sbert,s.__version__)"
nohup python eval/run_ab_30m_evaluation.py --config eval/configs/evaluation_config.json --output reports --seed 42 --force-full-run > reports/full_run_.log 2>&1 &

## Notes
- CPU-only torch to keep images small and reproducible.
- Fill in models/data later; skeleton is intentionally minimal.
