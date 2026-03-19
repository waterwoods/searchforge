# Vitals 数据流：Generator → Pub/Sub → Cloud Run 完整复盘

## 1. 一页概览 (One-Page Overview)

- **数据生成器** (`scripts/generate_vitals_stream.py`)：本地运行，生成模拟的生命体征数据（心率 HR、血氧 SpO2），输出 NDJSON 格式到 stdout
- **Pub/Sub Topic** (`vital-events`)：GCP 上的消息队列主题，接收生成器发送的 JSON 消息
- **Pub/Sub Subscription** (`vital-events-sub`)：订阅主题，Cloud Run 服务从这里拉取消息
- **Cloud Run 服务** (`services/vitals_viewer/main.py`)：部署在 GCP 上的 FastAPI 服务，从订阅中拉取消息并渲染成 HTML/JSON
- **本地组件**：生成器脚本（Python）、gcloud CLI（用于发布消息）
- **GCP 组件**：Pub/Sub Topic/Subscription、Cloud Run 服务
- **数据流**：Generator stdout → shell pipe → `gcloud pubsub topics publish` → Topic → Subscription → Cloud Run pull → HTML/JSON
- **认证方式**：本地使用 ADC (Application Default Credentials)，Cloud Run 使用服务账号自动认证
- **消息格式**：每行一个 JSON 对象，包含 `hr`, `spo2`, `time_ms`, `time_str`, `source` 字段
- **消息生命周期**：发布到 Topic → 推送到 Subscription → Cloud Run 拉取并 ACK → 消息消失（不会重复出现）
- **部署方式**：使用 `scripts/deploy_vitals_viewer.sh` 部署 Cloud Run 服务
- **查看结果**：访问 Cloud Run 提供的 HTTPS URL，刷新页面即可看到最新数据

---

## 2. 发布原理 (How Publishing Works - 核心原理)

### 2.1 生成器输出 NDJSON

生成器 (`scripts/generate_vitals_stream.py`) 在 `stdout` 模式下，每 2 秒（可配置）输出一行 JSON 到标准输出：

```python
# scripts/generate_vitals_stream.py, line 216-218
if self.mode == 'stdout':
    print(json.dumps(reading))
    sys.stdout.flush()
```

每行 JSON 格式示例：
```json
{"hr": 72.5, "spo2": 97.2, "time_ms": 1704067200000, "time_str": "2024-01-01 12:00:00", "source": "esp32-livingroom"}
```

### 2.2 Shell Pipe 循环发布到 Pub/Sub

使用 shell 管道 + while 循环，逐行读取并发布到 Pub/Sub topic：

```bash
# 发布命令（从生成器输出到 Pub/Sub）
python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 180 --interval-sec 2.0 | \
while IFS= read -r line; do
  gcloud pubsub topics publish vital-events --message="$line"
done
```

**命令说明**：
- `generate_vitals_stream.py --mode stdout`：生成器输出 NDJSON 到 stdout
- `--duration-sec 180`：运行 180 秒（3 分钟）
- `--interval-sec 2.0`：每 2 秒生成一条数据
- `while read -r line`：逐行读取生成器的输出
- `gcloud pubsub topics publish vital-events --message="$line"`：将每行 JSON 发布到 topic `vital-events`

### 2.3 Topic 和 Subscription 名称

- **Topic**: `vital-events`
- **Subscription**: `vital-events-sub`

### 2.4 为什么旧消息会消失？

Pub/Sub 是**队列模型**：
1. 消息发布到 Topic 后，会推送到所有订阅该 Topic 的 Subscription
2. Cloud Run 服务调用 `subscriber.pull()` 从 Subscription 拉取消息
3. 拉取后，服务调用 `subscriber.acknowledge()` **确认消息**（ACK）
4. **ACK 后的消息会从 Subscription 中删除**，不会再次出现
5. 如果消息未被 ACK，会在一定时间后重新投递（at-least-once delivery）

**代码位置**：
```python
# services/vitals_viewer/main.py, line 58-65
if ack_ids:
    subscriber.acknowledge(
        request={
            "subscription": subscription_path,
            "ack_ids": ack_ids,
        }
    )
```

---

## 3. Cloud Run Viewer 读取原理 (How Cloud Run Viewer Reads - 核心原理)

### 3.1 拉取消息

当用户访问 Cloud Run URL 时，服务调用 `pull_messages()` 函数：

```python
# services/vitals_viewer/main.py, line 22-70
def pull_messages(limit: int = 20) -> List[dict]:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    messages = []
    
    try:
        # Pull messages with immediate return (no waiting)
        response = subscriber.pull(
            request={
                "subscription": subscription_path,
                "max_messages": limit,
            }
        )
        
        ack_ids = []
        for received_message in response.received_messages:
            try:
                # Parse JSON message
                import json
                data = json.loads(received_message.message.data.decode('utf-8'))
                messages.append(data)
                ack_ids.append(received_message.ack_id)
            except (json.JSONDecodeError, KeyError) as e:
                # Skip invalid messages but still ack them
                ack_ids.append(received_message.ack_id)
        
        # Acknowledge messages
        if ack_ids:
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": ack_ids,
                }
            )
    except Exception as e:
        # Log error but don't crash
        print(f"Error pulling messages: {e}")
    
    return messages
```

### 3.2 解析和排序

拉取到的消息按 `time_ms` 降序排序（最新的在前）：

```python
# services/vitals_viewer/main.py, line 75-80
sorted_messages = sorted(
    messages,
    key=lambda x: x.get('time_ms', 0),
    reverse=True
)
```

### 3.3 渲染 HTML/JSON

根据 URL 参数决定返回 HTML 还是 JSON：

```python
# services/vitals_viewer/main.py, line 193-216
@app.get("/", response_class=HTMLResponse)
async def root(format: Optional[str] = Query(None, description="Output format: json or html")):
    messages = pull_messages(limit=20)
    
    if format == "json":
        # Sort by time_ms descending
        sorted_messages = sorted(
            messages,
            key=lambda x: x.get('time_ms', 0),
            reverse=True
        )
        return JSONResponse(content={
            "count": len(sorted_messages),
            "messages": sorted_messages
        })
    else:
        html = render_html(messages)
        return HTMLResponse(content=html)
```

---

## 4. GCP 认证说明 (GCP Authentication - 认证)

### 4.1 ADC (Application Default Credentials) 是什么？

ADC 是 Google Cloud 的**默认凭证机制**，让应用程序自动找到并使用合适的凭证，无需手动配置 API Key。

### 4.2 本地机器登录（WSL 流程）

在本地机器上，使用以下命令登录：

```bash
gcloud auth application-default login --no-launch-browser
```

**为什么用 `--no-launch-browser`？**
- WSL 环境下无法自动打开浏览器
- 命令会打印一个 URL，手动在 Windows 浏览器中打开完成 OAuth 流程

### 4.3 凭证存储位置

登录后，凭证保存在：
```
~/.config/gcloud/application_default_credentials.json
```

这个文件包含 OAuth token，用于访问 GCP 服务。

### 4.4 没有 API Key

**重要**：我们**不使用 API Key**。而是使用：
- **OAuth 2.0**：通过 `gcloud auth application-default login` 获取用户凭证
- **ADC**：应用程序自动读取 `~/.config/gcloud/application_default_credentials.json`

### 4.5 Cloud Run 的认证（高级说明）

Cloud Run 服务运行时：
- 使用**服务账号**（Service Account）作为身份
- 服务账号自动拥有访问 Pub/Sub 的权限（通过 IAM 配置）
- **无需手动配置凭证**，Cloud Run 运行时环境自动处理

**代码中无需显式配置**：
```python
# services/vitals_viewer/main.py, line 32
subscriber = pubsub_v1.SubscriberClient()
# 自动使用 Cloud Run 的服务账号凭证
```

---

## 5. 最小复现清单 (Minimal Reproduction)

### 5.1 前置条件检查

```bash
# 1. 设置 GCP 项目
gcloud config set project optimal-disk-472305-e2

# 2. 确保 Topic 和 Subscription 存在
gcloud pubsub topics describe vital-events
gcloud pubsub subscriptions describe vital-events-sub

# 3. 如果不存在，创建它们
gcloud pubsub topics create vital-events
gcloud pubsub subscriptions create vital-events-sub --topic=vital-events

# 4. 确保已登录 ADC（本地测试需要）
gcloud auth application-default login --no-launch-browser
```

### 5.2 发布数据（运行 180 秒）

```bash
# 发布数据到 Pub/Sub，持续 180 秒
python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 180 --interval-sec 2.0 | \
while IFS= read -r line; do
  gcloud pubsub topics publish vital-events --message="$line"
done
```

### 5.3 查看结果

1. **获取 Cloud Run URL**（如果已部署）：
   ```bash
   gcloud run services describe vitals-viewer --region us-central1 --format 'value(status.url)'
   ```

2. **在浏览器中打开 URL**，或使用 curl：
   ```bash
   # HTML 格式
   curl https://vitals-viewer-xxxxx-uc.a.run.app
   
   # JSON 格式
   curl https://vitals-viewer-xxxxx-uc.a.run.app/?format=json | jq
   ```

3. **刷新页面**即可看到最新数据

### 5.4 验证消息已发布

```bash
# 检查 Subscription 中是否有消息
gcloud pubsub subscriptions pull vital-events-sub --limit=5
```

---

## 相关文件清单

- `scripts/generate_vitals_stream.py` - 数据生成器
- `services/vitals_viewer/main.py` - Cloud Run 服务主程序
- `scripts/deploy_vitals_viewer.sh` - 部署脚本
- `docs/vitals_fake_stream.md` - 生成器文档
- `docs/vitals_viewer_cloud_run.md` - Cloud Run 服务文档
