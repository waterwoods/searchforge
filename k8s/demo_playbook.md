# K8S Demo Playbook（练习小抄）

本文件是给作者自己练习和面试 demo 用的速查表。面试时可以现场执行 Demo 1 和 Demo 2，如果有时间再讲 HPA 配置。假设集群名是 `searchforge-dev`，服务是 `ecommerce-agent-api`。

## 预备条件 / Prerequisites

- kind 集群已创建：`kind create cluster --name searchforge-dev`
- 镜像已构建并加载：`searchforge-ecommerce-api:latest`
- 已执行：`kubectl apply -f k8s/`

---

## Demo 1：自愈 / Self-healing

**Goal 目标：** 手动删掉 Pod，观察 Deployment 自动拉起新的 Pod。

**Commands：**

```bash
# 查看 Pod
kubectl get pods -l app=ecommerce-agent-api

# 删除 Pod（名字示例，练习前先用 get pods 确认）
POD_NAME=$(kubectl get pods -l app=ecommerce-agent-api -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $POD_NAME

# 反复查看，直到新的 Pod 变成 Running
kubectl get pods -l app=ecommerce-agent-api -w
```

**观察要点：** 旧 Pod 状态变为 `Terminating`，几秒后新 Pod 自动创建并启动，最终变为 `Running` 和 `Ready`。

---

## Demo 2：滚动发布 / Rolling update

**Goal 目标：** 修改 APP_VERSION，触发滚动更新，观察旧 Pod 退场、新 Pod 上线。

**Commands：**

```bash
# 方法 1：使用 kubectl edit（快速修改）
kubectl edit deployment ecommerce-agent-api
# 在 spec.template.spec.containers[0].env 中，找到 APP_VERSION，把 value 从 "v1" 改成 "v2"
# 保存后自动触发滚动更新

# 方法 2：修改文件后 apply（推荐用于实际部署）
# 编辑 k8s/deployment.yaml，修改 APP_VERSION 为 "v2"，然后：
kubectl apply -f k8s/deployment.yaml

# 观察滚动更新过程
kubectl rollout status deployment/ecommerce-agent-api

# 在另一个终端实时观察 Pod 变化
kubectl get pods -l app=ecommerce-agent-api -w
```

**观察要点：** 新 Pod 先被创建并通过 readinessProbe，旧 Pod 开始 Terminating，最终所有 Pod 都是新版本。`maxUnavailable: 0` 确保更新过程中始终有 Pod 可用。

---

## Demo 3：HPA / Horizontal Pod Autoscaler

**Goal 目标：** 展示 HPA 配置和基本行为（如果安装了 metrics-server，可以配合压测）。

**Commands：**

```bash
# 查看 HPA 状态
kubectl get hpa ecommerce-agent-api-hpa

# 查看 HPA 详细信息
kubectl describe hpa ecommerce-agent-api-hpa

# （可选）安装 metrics-server（如果当前集群没有）
# kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# （可选）启动一个简单压测（这里只做 TODO 提示，具体压测脚本可以后补充）
# TODO: run simple load test against /api/ecommerce-agent/run
# 例如：while true; do curl -X POST http://localhost:8080/api/ecommerce-agent/run ...; done

# 观察 HPA 是否调整 replica 数
kubectl get hpa ecommerce-agent-api-hpa -w

# 同时观察 Pod 数量变化
kubectl get pods -l app=ecommerce-agent-api -w
```

**观察要点：** HPA 监控 CPU 使用率（目标 60%），当 CPU 超过阈值时自动增加 Pod 数量（最多到 `maxReplicas: 3`），负载降低后自动减少（最少到 `minReplicas: 1`）。

**注意：** 如果集群没有 metrics-server，HPA 无法获取 CPU 指标，但 YAML 配置本身是正确的，可以在面试时作为概念和配置示例展示。

---

## 快速参考 / Quick Reference

```bash
# 查看所有资源
kubectl get all -l app=ecommerce-agent-api

# 查看 Pod 日志
kubectl logs -f deployment/ecommerce-agent-api

# 查看 Deployment 详情
kubectl describe deployment ecommerce-agent-api

# Port-forward 测试
kubectl port-forward deployment/ecommerce-agent-api 8080:8000

# 回滚到上一个版本（如果滚动更新出问题）
kubectl rollout undo deployment/ecommerce-agent-api
```
