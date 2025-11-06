# Docker Disk Cleanup Utilities

安全清理 Docker 磁盘空间的工具脚本，默认 dry-run 模式，需要显式设置 `RUN=1` 才会真正删除。

## 功能特性

- ✅ **默认 dry-run 模式**：安全预览，不会误删
- ✅ **保护关键卷**：默认保留 `qdrant|milvus|minio|redis|postgres` 等持久化卷
- ✅ **可配置过滤**：通过环境变量自定义保留卷的正则表达式
- ✅ **年龄过滤**：只清理指定时间之前的资源（默认 240 小时 = 10 天）
- ✅ **空间报告**：清理前后显示磁盘使用情况

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RUN` | `0` | `0` = dry-run（只预览），`1` = 真正执行删除 |
| `AGE_HOURS` | `240` | 只清理 N 小时之前的资源（240h = 10天） |
| `KEEP_VOLUMES_REGEX` | `"(qdrant\|milvus\|minio\|redis\|postgres)"` | 需要保留的卷名正则表达式 |
| `PRUNE_BUILDX` | `1` | 是否清理 buildx 构建缓存（`1` = 是，`0` = 否） |

## 使用示例

### 1. 查看 Docker 空间使用报告

```bash
make docker-space
```

### 2. 预览清理内容（dry-run，不实际删除）

```bash
make docker-clean
```

### 3. 真正执行清理（保留 qdrant/milvus/minio/redis 等卷）

```bash
RUN=1 make docker-clean
```

### 4. 清理更旧的资源（例如只保留 3 天内的）

```bash
RUN=1 AGE_HOURS=72 make docker-clean
```

### 5. 激进清理（清理所有历史，但仍保留关键卷）

```bash
RUN=1 make docker-clean-all
```

### 6. 自定义清理时间阈值

```bash
# 清理 1 周之前的资源
AGE_HOURS=168 RUN=1 make docker-prune-old
```

### 7. 自定义需要保留的卷

```bash
# 除了默认的，还保留包含 "mysql" 或 "elasticsearch" 的卷
KEEP_VOLUMES_REGEX="(qdrant|milvus|minio|redis|postgres|mysql|elasticsearch)" RUN=1 make docker-clean
```

## 清理内容

脚本会安全清理以下资源（仅限已停止/悬空/未使用的）：

- ✅ 已停止的容器（不会影响运行中的容器）
- ✅ 悬空/旧的镜像
- ✅ 未使用的网络
- ✅ 构建缓存（如果 `PRUNE_BUILDX=1`）
- ✅ 悬空的卷（排除 `KEEP_VOLUMES_REGEX` 匹配的卷）

**⚠️ 安全保证：**
- 不会停止运行中的容器
- 不会删除有状态服务的关键卷（qdrant/milvus/minio/redis/postgres 等）
- 默认 dry-run 模式，需要显式设置 `RUN=1` 才会真正删除

## 直接调用脚本

也可以直接调用脚本（不通过 Makefile）：

```bash
# 查看报告
bash scripts/docker/space_report.sh

# 清理（dry-run）
bash scripts/docker/clean.sh

# 清理（真正执行）
RUN=1 bash scripts/docker/clean.sh

# 自定义参数
RUN=1 AGE_HOURS=72 KEEP_VOLUMES_REGEX="(qdrant|mysql)" bash scripts/docker/clean.sh
```

## 注意事项

1. **首次使用建议先 dry-run**：运行 `make docker-clean` 预览将要清理的内容
2. **保护关键卷**：如果环境中有其他重要的持久化卷，记得更新 `KEEP_VOLUMES_REGEX`
3. **备份重要数据**：虽然脚本会保护关键卷，但执行清理前建议备份重要数据
4. **macOS/Linux 兼容**：脚本使用标准 bash，兼容 macOS 和 Linux





