# K8S 实战小故事：从本地 Agent 到生产级部署

## 1. 项目背景

我有一个基于 FastAPI + LangGraph 的电商退款智能体（ecommerce refund agent），之前跑在本机或 Docker 容器里。这次的目标是把它做成一个"像生产一样"的 K8S 部署，可以在面试里讲清楚我懂容器化 + K8S 基础能力。整个实战是在本地 RTX3080 上，用 kind 搭建的 K8S 集群完成的。

## 2. 整体架构

```
┌─────────────────┐
│  Docker Image    │  searchforge-ecommerce-api:latest
│  (Dockerfile)    │  → 暴露 8000 端口，入口 uvicorn
└────────┬─────────┘
         │ kind load
         ▼
┌─────────────────┐
│  kind Cluster   │  searchforge-dev
│  (本地 K8S)     │
└────────┬─────────┘
         │ kubectl apply
         ▼
┌─────────────────┐      ┌──────────────┐
│  Deployment     │─────▶│   Service    │  ClusterIP:80 → Pod:8000
│  (3 replicas)  │      │              │
└────────┬────────┘      └──────┬───────┘
         │                      │
         │                      │ port-forward
         │                      ▼
         │              ┌──────────────┐
         │              │  客户端 curl  │  localhost:8080
         │              └──────────────┘
         │
         ▼
┌─────────────────┐
│  Pod (容器)     │  ecommerce-agent-api-xxxxx
│  - ConfigMap    │  (LOG_LEVEL, LANGSMITH_PROJECT)
│  - Secret       │  (OPENAI_API_KEY)
│  - Probes       │  (/healthz, /readyz)
│  - Resources    │  (requests/limits)
└─────────────────┘
```

**架构说明：** 整个流程从 Docker 镜像构建开始，通过 `kind load` 把镜像加载到本地 K8S 集群。然后通过 `kubectl apply` 部署 Deployment、Service、ConfigMap、Secret 等资源。Deployment 管理 Pod 的生命周期，Service 提供内部服务发现，最后通过 `port-forward` 暴露给本地客户端测试。应用名是 `ecommerce-agent-api`，运行在 `searchforge-dev` 集群里。

## 3. 我做了哪些具体工作

### 容器化
- **新写 Dockerfile.ecommerce**：基于 `python:3.11-slim`，只打包需要的代码和依赖（services/fiqa_api、engines、agents 等），暴露 8000 端口，入口是 `uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8000`。
- **镜像构建**：`docker build -f Dockerfile.ecommerce -t searchforge-ecommerce-api:latest .`
- **加载到 kind**：`kind load docker-image searchforge-ecommerce-api:latest --name searchforge-dev`

### K8S 清单文件
在 `k8s/` 目录下写了完整的 K8S 资源清单：
- **deployment.yaml**：定义 Pod 模板、副本数、滚动更新策略（`maxUnavailable: 0`，`maxSurge: 1`）
- **service.yaml**：ClusterIP 类型，端口 80 → 8000，提供内部服务发现
- **configmap.yaml**：存储非敏感配置（`LOG_LEVEL: "info"`，`LANGSMITH_PROJECT: "searchforge-ecommerce-dev"`）
- **secret-example.yaml**：Secret 模板，实际用 `kubectl create secret` 创建（包含 `OPENAI_API_KEY`、`LANGSMITH_API_KEY`）
- **hpa.yaml**：HorizontalPodAutoscaler，基于 CPU 使用率自动扩缩容（1-3 个副本，目标 60%）

### 健康检查
在 Deployment 里配置了完整的探针：
- **livenessProbe**：`/healthz` 端点，`initialDelaySeconds: 40`，`periodSeconds: 10`，失败 3 次后重启 Pod
- **readinessProbe**：`/readyz` 端点，`initialDelaySeconds: 20`，`periodSeconds: 5`，确保 Pod 就绪后才接收流量

### 安全配置
- **Secret 注入**：`OPENAI_API_KEY` 和 `LANGSMITH_API_KEY` 通过 `secretKeyRef` 注入到 Pod 环境变量，避免硬编码
- **ConfigMap 注入**：`LOG_LEVEL` 和 `LANGSMITH_PROJECT` 通过 `configMapKeyRef` 注入，支持运行时配置变更

### 资源与自动伸缩
- **资源限制**：给 Pod 配置了 `requests`（memory: 256Mi, cpu: 100m）和 `limits`（memory: 2Gi, cpu: 1000m），防止单个 Pod 拖垮节点
- **HPA 配置**：HorizontalPodAutoscaler 监控 CPU 使用率，目标 60%，自动在 1-3 个副本之间扩缩容

## 4. 三个 Demo（面试重点）

### Demo 1：自愈（Self-healing）

**演示步骤：**
1. 查看当前运行的 Pod：`kubectl get pods -l app=ecommerce-agent-api`
2. 手动删除 Pod：`kubectl delete pod <pod-name>`
3. 观察 Deployment 自动拉起新的 Pod：`kubectl get pods -l app=ecommerce-agent-api -w`

**观察要点：** 旧 Pod 状态变为 `Terminating`，几秒后新 Pod 自动创建并启动，经过 `readinessProbe` 检查后变为 `Ready` 状态，服务不中断。这展示了 Kubernetes 的声明式管理和自愈能力。

### Demo 2：滚动发布（Rolling Update）

**演示步骤：**
1. 修改 `deployment.yaml` 里的 `APP_VERSION` 从 `"v3"` 改为 `"v4"`
2. 应用更新：`kubectl apply -f k8s/deployment.yaml`
3. 观察滚动更新：`kubectl rollout status deployment/ecommerce-agent-api`
4. 实时观察 Pod 变化：`kubectl get pods -l app=ecommerce-agent-api -w`

**观察要点：** 新 Pod 先被创建（`maxSurge: 1`），通过 `readinessProbe` 后变为 Ready，然后旧 Pod 开始 Terminating（`maxUnavailable: 0` 确保始终有 Pod 可用），最终所有 Pod 都是新版本。这展示了零停机部署的能力。

### Demo 3：自动扩缩容（HPA）

**演示步骤：**
1. 应用 HPA 配置：`kubectl apply -f k8s/hpa.yaml`
2. 查看 HPA 状态：`kubectl get hpa ecommerce-agent-api-hpa`
3. （可选）制造 CPU 压力：持续发送请求到 `/api/ecommerce-agent/run`
4. 观察 HPA 调整副本数：`kubectl get hpa ecommerce-agent-api-hpa -w` 和 `kubectl get pods -l app=ecommerce-agent-api -w`

**观察要点：** HPA 监控 CPU 使用率（目标 60%），当平均 CPU 超过阈值时自动增加 Pod 数量（最多到 `maxReplicas: 3`），负载降低后自动减少（最少到 `minReplicas: 1`）。这展示了 Kubernetes 的弹性伸缩能力。

## 5. 我能向面试官怎么讲

### 中文版

我从一个本地的 LLM agent 服务出发，自己动手完成了 Docker 化、K8S 部署、健康检查、自愈、滚动发布和 HPA 配置。整个过程包括：用 Dockerfile 把 FastAPI + LangGraph 应用打包成镜像，在本地 kind 集群里部署 Deployment 和 Service，配置了 liveness/readiness probe 确保服务健康，用 Secret 和 ConfigMap 管理敏感和非敏感配置，设置了资源 requests/limits 防止资源耗尽，最后还配置了 HPA 实现自动扩缩容。通过三个实际 demo（自愈、滚动发布、HPA），我验证了 K8S 的核心能力，也理解了生产环境里容器编排的关键点。

### English Version

I took a local ecommerce LLM agent built with FastAPI and LangGraph, and turned it into a production-style deployment on Kubernetes using kind. The process involved containerizing the application with a custom Dockerfile, deploying it to a local K8S cluster with Deployment and Service resources, configuring liveness and readiness probes for health monitoring, using Secrets and ConfigMaps for secure configuration management, setting resource requests and limits to prevent resource exhaustion, and implementing HPA for automatic scaling. Through three practical demos (self-healing, rolling updates, and HPA), I validated Kubernetes' core capabilities and gained hands-on experience with container orchestration concepts that are essential in production environments. The deployment demonstrates my understanding of key K8S concepts including declarative management, zero-downtime deployments, and elastic scaling.

---

**关键术语回顾：** Deployment / Service / ConfigMap / Secret / livenessProbe / readinessProbe / RollingUpdate / maxUnavailable / maxSurge / HorizontalPodAutoscaler (HPA) / resource requests/limits / kind / port-forward
