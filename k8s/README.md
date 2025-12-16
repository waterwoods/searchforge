# Kubernetes Deployment Guide for Ecommerce Agent API

This guide walks you through deploying the ecommerce refund agent HTTP API to a local Kubernetes cluster (kind or minikube).

## 📋 Prerequisites

- Docker installed and running
- Kubernetes cluster (kind or minikube)
- `kubectl` configured to access your cluster
- OpenAI API key (for the agent)

## 🚀 Step-by-Step Deployment

### Step 1: Start a Local Kubernetes Cluster

#### Option A: Using kind (recommended)

```bash
# Create a kind cluster
kind create cluster --name searchforge-dev

# Verify cluster is running
kubectl cluster-info --context kind-searchforge-dev
```

#### Option B: Using minikube

```bash
# Start minikube
minikube start

# Verify cluster is running
kubectl cluster-info
```

### Step 2: Build the Docker Image

Build the Docker image for the ecommerce agent API:

```bash
# From the project root
docker build -f Dockerfile.ecommerce -t searchforge-ecommerce-api:latest .
```

### Step 3: Load Image into Kubernetes Cluster

#### For kind:

```bash
kind load docker-image searchforge-ecommerce-api:latest --name searchforge-dev
```

#### For minikube:

```bash
# Set Docker environment to use minikube's Docker daemon
eval $(minikube docker-env)

# Build the image again (this time it goes into minikube's Docker)
docker build -f Dockerfile.ecommerce -t searchforge-ecommerce-api:latest .

# Unset minikube Docker environment (optional, to return to local Docker)
eval $(minikube docker-env -u)
```

### Step 4: Create the Secret

Create a Kubernetes Secret with your OpenAI API key:

```bash
kubectl create secret generic ecommerce-agent-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-actual-key-here \
  --from-literal=LANGSMITH_API_KEY=lsv2_pt_your-key-here
```

**Note:** Replace `sk-your-actual-key-here` with your real OpenAI API key. The `LANGSMITH_API_KEY` is optional but recommended for observability.

Alternatively, you can edit `secret-example.yaml`, replace `REPLACE_ME` values, and apply it:

```bash
# Edit secret-example.yaml first, then:
kubectl apply -f k8s/secret-example.yaml
```

### Step 5: Apply Kubernetes Manifests

Apply all Kubernetes manifests:

```bash
# Apply ConfigMap (optional LangSmith config)
kubectl apply -f k8s/configmap.yaml

# Apply Deployment and Service
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Or apply all at once:

```bash
kubectl apply -f k8s/
```

### Step 6: Verify Deployment

Check that the pods are running:

```bash
# Check pod status
kubectl get pods -l app=ecommerce-agent-api

# Check pod logs
kubectl logs -l app=ecommerce-agent-api --tail=50

# Check deployment status
kubectl get deployment ecommerce-agent-api
```

Wait for the pod to be in `Running` state and `Ready` (1/1):

```bash
# Watch pod status
kubectl get pods -l app=ecommerce-agent-api -w
```

### Step 7: Port Forward and Test

Port-forward the service to access it locally:

```bash
# Port-forward the deployment (maps local 8080 to pod's 8000)
kubectl port-forward deployment/ecommerce-agent-api 8080:8000
```

In another terminal, test the health endpoint:

```bash
# Test health check
curl http://localhost:8080/healthz

# Test readiness check
curl http://localhost:8080/readyz
```

### Step 8: Test the Ecommerce Agent Endpoint

Test the main ecommerce agent endpoint:

```bash
curl -X POST http://localhost:8080/api/ecommerce-agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "AMZ10001",
    "user_message": "I want a refund for my order"
  }'
```

Expected response:

```json
{
  "order_id": "AMZ10001",
  "final_response": "...",
  "refund_eligible": true,
  "refund_amount": 50.0,
  "currency": "USD"
}
```

## 🎬 Kubernetes 功能演示（Demo）

以下章节展示了几个关键的 Kubernetes 功能，适合在面试或技术分享时演示。

> 💡 **快速练习小抄：** 如需快速命令参考，可查看 [demo_playbook.md](./demo_playbook.md)，该文件提供了简洁的命令列表，适合练习和面试前速查。

### Demo 1：Pod 自愈（Self-healing）

**原理：** Deployment + livenessProbe = Pod 挂了会被自动重建

Kubernetes 通过 `livenessProbe` 定期检查 Pod 的健康状态。如果 Pod 不健康，Kubernetes 会自动重启或重建 Pod，确保服务的高可用性。

**演示步骤：**

```bash
# 1. 查看当前运行的 Pod
kubectl get pods -l app=ecommerce-agent-api

# 2. 记录 Pod 名称（例如：ecommerce-agent-api-xxxxx-xxxxx）
POD_NAME=$(kubectl get pods -l app=ecommerce-agent-api -o jsonpath='{.items[0].metadata.name}')
echo "Pod name: $POD_NAME"

# 3. 删除这个 Pod（模拟 Pod 故障）
kubectl delete pod $POD_NAME

# 4. 立即再次查看 Pod 状态
kubectl get pods -l app=ecommerce-agent-api -w

# 你会看到：
# - 旧 Pod 状态变为 Terminating
# - 几秒后，新的 Pod 自动被创建并启动
# - 新 Pod 经过 readinessProbe 检查后变为 Ready 状态
```

**观察要点：**

- 删除 Pod 后，Deployment 会自动创建新的 Pod 来维持 `replicas: 1` 的期望状态
- `readinessProbe` 确保新 Pod 完全就绪后才接收流量
- `livenessProbe` 会持续监控 Pod 健康，如果应用崩溃会自动重启

**相关配置位置：** `k8s/deployment.yaml` 中的 `livenessProbe` 和 `readinessProbe` 字段

---

### Demo 2：滚动发布（Rolling Update）

**原理：** `maxUnavailable=0` 表示不会中断线上流量，更新是渐进式的

滚动更新策略确保在更新应用版本时，始终保持有可用的 Pod 处理请求，实现零停机部署。

**演示步骤：**

```bash
# 1. 查看当前部署状态和版本
kubectl get deployment ecommerce-agent-api
kubectl get pods -l app=ecommerce-agent-api -o jsonpath='{.items[0].spec.containers[0].env[?(@.name=="APP_VERSION")].value}'

# 2. 修改 deployment.yaml，将 APP_VERSION 从 "v1" 改为 "v2"
# 编辑 k8s/deployment.yaml，找到：
#   - name: APP_VERSION
#     value: "v1"
# 改为：
#   - name: APP_VERSION
#     value: "v2"

# 3. 应用更新
kubectl apply -f k8s/deployment.yaml

# 4. 观察滚动更新过程
kubectl rollout status deployment/ecommerce-agent-api

# 5. 在另一个终端实时观察 Pod 变化
kubectl get pods -l app=ecommerce-agent-api -w

# 你会看到：
# - 新 Pod 先被创建（maxSurge: 1）
# - 新 Pod 通过 readinessProbe 后变为 Ready
# - 旧 Pod 开始终止（maxUnavailable: 0 确保始终有 Pod 可用）
# - 最终所有 Pod 都是新版本
```

**观察要点：**

- `maxSurge: 1` 允许在更新时临时增加 1 个 Pod
- `maxUnavailable: 0` 确保更新过程中始终有 Pod 可用，不会中断服务
- 更新是渐进式的，旧 Pod 在新 Pod 就绪后才被终止

**相关配置位置：** `k8s/deployment.yaml` 中的 `strategy.rollingUpdate` 字段

---

### Demo 3：自动扩缩容（Horizontal Pod Autoscaler, HPA）

**原理：** HPA 根据 CPU/内存使用率自动调整 Pod 数量，实现弹性伸缩

**前置条件（可选）：** 需要 metrics-server 来提供资源指标。kind 集群默认可能没有，但可以安装：

```bash
# 为 kind 集群安装 metrics-server（可选）
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**演示步骤：**

```bash
# 1. 应用 HPA 配置
kubectl apply -f k8s/hpa.yaml

# 2. 查看 HPA 状态
kubectl get hpa ecommerce-agent-api-hpa

# 3. 查看 HPA 详细信息
kubectl describe hpa ecommerce-agent-api-hpa

# 4. 制造 CPU 压力（模拟负载）
# 在一个终端持续发送请求：
while true; do
  kubectl port-forward deployment/ecommerce-agent-api 8080:8000 &
  PF_PID=$!
  sleep 2
  for i in {1..10}; do
    curl -X POST http://localhost:8080/api/ecommerce-agent/run \
      -H "Content-Type: application/json" \
      -d '{"order_id": "AMZ10001", "user_message": "test"}' > /dev/null 2>&1
  done
  kill $PF_PID 2>/dev/null
  sleep 5
done

# 5. 在另一个终端观察 HPA 和 Pod 数量变化
watch -n 2 'kubectl get hpa ecommerce-agent-api-hpa && echo "" && kubectl get pods -l app=ecommerce-agent-api'

# 你会看到：
# - CPU 使用率上升时，HPA 会自动增加 Pod 数量（最多到 maxReplicas: 3）
# - 负载降低后，HPA 会自动减少 Pod 数量（最少到 minReplicas: 1）
```

**观察要点：**

- HPA 监控 CPU 使用率，目标设置为 60%
- 当平均 CPU 使用率超过 60% 时，HPA 会增加 Pod 数量
- 当 CPU 使用率降低时，HPA 会逐步减少 Pod 数量
- `minReplicas: 1` 和 `maxReplicas: 3` 限制了扩缩容的范围

**相关配置位置：** `k8s/hpa.yaml` 和 `k8s/deployment.yaml` 中的 `resources` 字段

**注意：** 如果集群没有 metrics-server，HPA 无法获取 CPU 指标，但 YAML 配置本身是正确的，可以在面试时作为概念和配置示例展示。

---

### Demo 4：配置 & Secret & 资源限制

**原理：** ConfigMap 存非敏感配置，Secret 存敏感信息，Resources 防止单个 Pod 拖垮节点

Kubernetes 提供了多种方式来管理应用配置和资源使用，确保安全性和稳定性。

#### ConfigMap（非敏感配置）

ConfigMap 用于存储非敏感的配置数据，如日志级别、项目名称等。

**查看当前 ConfigMap：**

```bash
# 查看 ConfigMap 内容
kubectl get configmap ecommerce-agent-config -o yaml

# 查看特定配置项
kubectl get configmap ecommerce-agent-config -o jsonpath='{.data.LOG_LEVEL}'
```

**修改配置：**

```bash
# 方法 1：直接编辑 ConfigMap
kubectl edit configmap ecommerce-agent-config

# 方法 2：修改 YAML 文件后应用
# 编辑 k8s/configmap.yaml，然后：
kubectl apply -f k8s/configmap.yaml

# 修改后需要重启 Pod 才能生效（或使用滚动更新）
kubectl rollout restart deployment/ecommerce-agent-api
```

**当前 ConfigMap 包含：**
- `LANGSMITH_PROJECT`: LangSmith 项目名称
- `LOG_LEVEL`: 日志级别（info/debug/warning 等）

#### Secret（敏感信息）

Secret 用于存储敏感信息，如 API 密钥、密码等。Secret 数据是 base64 编码的，但不应直接提交到 Git。

**创建 Secret：**

```bash
# 推荐方式：使用 kubectl create（不会在文件中暴露密钥）
kubectl create secret generic ecommerce-agent-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key-here \
  --from-literal=LANGSMITH_API_KEY=lsv2_pt_your-key-here
```

**查看 Secret（注意：值会以 base64 编码显示）：**

```bash
# 查看 Secret 元数据（不显示值）
kubectl get secret ecommerce-agent-secrets

# 查看 Secret 的键名
kubectl get secret ecommerce-agent-secrets -o jsonpath='{.data}' | jq 'keys'

# 解码查看某个值（仅用于调试）
kubectl get secret ecommerce-agent-secrets -o jsonpath='{.data.OPENAI_API_KEY}' | base64 -d
```

**当前 Secret 包含：**
- `OPENAI_API_KEY`: OpenAI API 密钥（必需）
- `LANGSMITH_API_KEY`: LangSmith API 密钥（可选）

#### 资源限制（Resources）

资源限制确保 Pod 不会消耗过多 CPU 或内存，防止单个 Pod 拖垮整个节点。

**查看当前资源配置：**

```bash
# 查看 Pod 的资源请求和限制
kubectl describe pod -l app=ecommerce-agent-api | grep -A 5 "Limits\|Requests"

# 查看资源使用情况（需要 metrics-server）
kubectl top pod -l app=ecommerce-agent-api
```

**当前资源配置（在 deployment.yaml 中）：**

```yaml
resources:
  requests:      # 资源请求：调度器保证的最小资源
    memory: "256Mi"
    cpu: "100m"
  limits:        # 资源限制：Pod 最多能使用的资源
    memory: "2Gi"
    cpu: "1000m"
```

**说明：**
- `requests`: 调度器在分配 Pod 到节点时，会确保节点有足够的资源。这是 Pod 的"最低保障"
- `limits`: Pod 最多能使用的资源。超过限制时，Pod 可能被限流（CPU）或被 OOMKilled（内存）

**修改资源配置：**

```bash
# 编辑 deployment.yaml 中的 resources 字段，然后：
kubectl apply -f k8s/deployment.yaml
```

#### 配置注入方式

在 `deployment.yaml` 中，配置通过环境变量注入到容器：

```yaml
env:
  # 从 ConfigMap 读取
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: ecommerce-agent-config
        key: LOG_LEVEL
  # 从 Secret 读取
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: ecommerce-agent-secrets
        key: OPENAI_API_KEY
```

**相关配置文件：**
- `k8s/configmap.yaml`: ConfigMap 定义
- `k8s/secret-example.yaml`: Secret 示例（不要提交真实密钥）
- `k8s/deployment.yaml`: Deployment 中的 env 和 resources 配置

---

### Demo 5：简单压测 + SLO 对话

**原理：** 使用压测脚本验证系统在负载下的性能表现，结合 SLO（Service Level Objective）进行可观测性演示

通过简单的压测脚本，可以快速验证系统在并发负载下的延迟和错误率，这是设置和验证 SLO 的基础。

**演示步骤：**

```bash
# 在本地 8080 端口已经 port-forward 到 K8S Deployment 的前提下：
kubectl port-forward deployment/ecommerce-agent-api 8080:8000

# 运行压测脚本
python -m experiments.ecommerce.load_test_ecommerce \
  --url http://localhost:8080/api/ecommerce-agent/run \
  --concurrency 5 \
  --requests 50
```

**SLO 对话要点：**

在面试或技术分享时，可以这样介绍 SLO：

"For this demo I'd set an SLO like: '99% of requests under 500ms, error rate < 1% under normal load'. Then use this script to check if the system meets that under expected traffic. The script measures p50/p95 latency and success rate, which are key metrics for validating SLO compliance."

**观察要点：**

- 脚本会输出平均延迟、p50、p95 延迟和成功率
- 可以根据压测结果调整 HPA 的 CPU 阈值或资源限制
- 结合 Demo 3（HPA）可以演示在负载增加时系统的自动扩缩容能力

**相关文件：**
- `experiments/ecommerce/load_test_ecommerce.py`: 压测脚本

---

## 🔍 Troubleshooting

### Pod not starting

```bash
# Check pod events
kubectl describe pod -l app=ecommerce-agent-api

# Check logs
kubectl logs -l app=ecommerce-agent-api
```

### Health checks failing

```bash
# Check if the pod is receiving traffic
kubectl exec -it deployment/ecommerce-agent-api -- curl http://localhost:8000/healthz

# Check probe configuration
kubectl describe pod -l app=ecommerce-agent-api | grep -A 10 "Liveness\|Readiness"
```

### Secret not found

```bash
# Verify secret exists
kubectl get secret ecommerce-agent-secrets

# Check secret keys
kubectl get secret ecommerce-agent-secrets -o jsonpath='{.data}' | jq
```

### Image pull errors

For kind:
```bash
# Reload image
kind load docker-image searchforge-ecommerce-api:latest --name searchforge-dev
```

For minikube:
```bash
# Rebuild in minikube's Docker environment
eval $(minikube docker-env)
docker build -f Dockerfile.ecommerce -t searchforge-ecommerce-api:latest .
```

## 📝 Cleanup

To remove all resources:

```bash
# Delete deployment and service
kubectl delete -f k8s/

# Delete secret (optional)
kubectl delete secret ecommerce-agent-secrets

# Delete kind cluster (if using kind)
kind delete cluster --name searchforge-dev

# Or stop minikube (if using minikube)
minikube stop
```

## 🎯 Quick Reference

### Build and Run Locally (Docker)

```bash
# Build image
docker build -f Dockerfile.ecommerce -t searchforge-ecommerce-api .

# Run locally
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  searchforge-ecommerce-api

# Quick test
curl -X POST http://localhost:8000/api/ecommerce-agent/run \
  -H "Content-Type: application/json" \
  -d '{"order_id": "AMZ10001", "user_message": "I want a refund"}'
```

### Kubernetes Commands

```bash
# Apply all manifests
kubectl apply -f k8s/

# Port-forward
kubectl port-forward deployment/ecommerce-agent-api 8080:8000

# View logs
kubectl logs -f deployment/ecommerce-agent-api

# Scale deployment
kubectl scale deployment ecommerce-agent-api --replicas=2
```

## 🎯 JobHunter API 部署

JobHunter API 提供了一个独立的 serving 形态，用于职位描述分析和职业建议。

### 前置条件

- 已完成 ecommerce agent 的 Secret 创建（JobHunter 复用 `ecommerce-agent-secrets`）
- kind 集群 `searchforge-dev` 已创建并运行

### 部署步骤

#### 1. 构建 Docker 镜像

```bash
# 从项目根目录构建 JobHunter 镜像
docker build -f Dockerfile.jobhunter -t searchforge-jobhunter-api:latest .
```

#### 2. 加载镜像到 kind 集群

```bash
kind load docker-image searchforge-jobhunter-api:latest --name searchforge-dev
```

#### 3. 应用 Kubernetes 清单

```bash
# 应用 Deployment 和 Service
kubectl apply -f k8s/jobhunter-deployment.yaml
kubectl apply -f k8s/jobhunter-service.yaml
```

#### 4. 验证部署

```bash
# 查看 Pod 状态
kubectl get pods -l app=jobhunter-api

# 查看 Pod 日志
kubectl logs -l app=jobhunter-api --tail=50
```

等待 Pod 状态变为 `Running` 且 `Ready` (1/1)。

#### 5. Port Forward 并测试

```bash
# Port-forward（映射本地 8081 到 Pod 的 8000）
kubectl port-forward deployment/jobhunter-api 8081:8000
```

在另一个终端中测试：

```bash
# 测试健康检查
curl http://localhost:8081/healthz

# 测试就绪检查
curl http://localhost:8081/readyz

# 测试 JobHunter analyze 端点
curl -X POST http://localhost:8081/api/jobhunter/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "jd_input": {
      "description": "We are looking for a senior software engineer with 5+ years of experience in Python and FastAPI.",
      "title": "Senior Software Engineer",
      "company": "Example Corp",
      "location": "San Francisco, CA"
    },
    "use_default_profile": false
  }'
```

### 注意事项

- **Secret 复用**: JobHunter deployment 目前复用 `ecommerce-agent-secrets` Secret。在生产环境中，建议创建专用的 `jobhunter-agent-secrets` Secret。
- **资源配置**: 默认配置为 `requests: cpu: 100m, memory: 256Mi` 和 `limits: cpu: 1000m, memory: 2Gi`，可根据实际负载调整。
- **健康检查**: 使用 `/healthz` 和 `/readyz` 端点进行健康检查和就绪检查。

### JobHunter API – 简单压测 + SLO 检查

一旦 JobHunter API 在 kind 集群上运行并且 port-forward 已激活：

```bash
# 1) Port-forward JobHunter API (在一个终端)
kubectl port-forward deployment/jobhunter-api 8082:8000

# 2) 运行压测脚本 (在另一个终端)
python3 -m experiments.jobhunter.load_test_jobhunter \
  --url http://localhost:8082/api/jobhunter/analyze \
  --concurrency 2 \
  --requests 20
```

**参数说明：**
- 默认并发设置为 2（而不是 5），因为每个 JD 分析调用涉及 LLM，处理较重，2 并发更接近真实使用场景
- 请求超时设置为 120 秒，以适应 LLM 调用的延迟

脚本将输出：
- 总请求数、应用层请求数（真正到达服务器的请求）
- 成功率、平均延迟、p50、p95、QPS
- **Infra errors**（连接错误/超时）：这些错误不会计入 SLO 计算，因为它们是基础设施问题（如 port-forward 断开），而非应用本身的问题
- SLO 评估结果：PASS/FAIL（基于 99% 成功率和 p95 <= 1000ms 的阈值）

**SLO 规则：**
- 成功率 >= 99%（只计算到达服务器的请求）
- p95 延迟 <= 1000ms（只计算成功请求的延迟）
- **注意**：连接错误和超时（infra_errors）不会影响 SLO 判断，因为它们反映的是基础设施问题而非应用质量

**使用自定义 JD 文件：**

```bash
python3 -m experiments.jobhunter.load_test_jobhunter \
  --url http://localhost:8082/api/jobhunter/analyze \
  --concurrency 2 \
  --requests 20 \
  --jd-file /path/to/job_description.txt
```

如果不提供 `--jd-file`，脚本会使用内置的 JD 文本（包含 LLM/agents、GCP/BigQuery、数据管道/可观测性等内容）。

### 清理

```bash
# 删除 JobHunter 部署和服务
kubectl delete -f k8s/jobhunter-deployment.yaml
kubectl delete -f k8s/jobhunter-service.yaml
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kind Documentation](https://kind.sigs.k8s.io/)
- [minikube Documentation](https://minikube.sigs.k8s.io/docs/)

