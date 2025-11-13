set -e
sed -i 's/^USE_PROXY=.*/USE_PROXY=false/' .env.current
docker compose restart rag-api
curl -sf http://localhost:8000/healthz
echo "rollback done"
