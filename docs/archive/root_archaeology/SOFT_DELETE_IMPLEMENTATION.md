# 软删除实现总结

## 修改文件清单

### 后端修改

1. **`services/fiqa_api/jobhunter/sqlite_cache.py`**
   - `init_db()`: 添加了 `deleted` 字段的迁移逻辑（检查列是否存在，不存在则添加）
   - `get_job_application_by_cache_id()`: 在 WHERE 条件中添加 `AND deleted = 0` 过滤
   - `list_job_applications()`: 在 WHERE 条件中添加 `AND deleted = 0` 过滤
   - `delete_job_application()`: 从硬删除（DELETE）改为软删除（UPDATE deleted = 1, last_updated_at = CURRENT_TIMESTAMP）
   - `upsert_job_application()`: 更新时设置 `deleted = 0`，允许恢复已软删除的记录

### 前端修改

2. **`ui/src/pages/JobHunterPage.tsx`**
   - `handleUnmarkApplicationStatus()`: 为所有取消操作添加确认弹窗（之前只对 critical statuses 有确认）

## 实现细节

### 后端软删除实现

1. **数据库迁移**
   - 在 `init_db()` 中使用 `PRAGMA table_info()` 检查 `deleted` 列是否存在
   - 如果不存在，执行 `ALTER TABLE job_applications ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0`
   - 保证幂等性，多次调用不会报错

2. **查询过滤**
   - 所有查询 `job_applications` 的函数都添加了 `AND deleted = 0` 条件
   - 确保前端不会看到已软删除的记录

3. **软删除操作**
   - `delete_job_application()` 现在执行：
     ```sql
     UPDATE job_applications
     SET deleted = 1,
         last_updated_at = CURRENT_TIMESTAMP
     WHERE user_id = ? AND profile_id = ? AND cache_id = ? AND deleted = 0
     ```
   - 只更新 `deleted = 0` 的记录，避免重复软删除

4. **恢复软删除记录**
   - `upsert_job_application()` 在更新时会设置 `deleted = 0`
   - 如果用户对一个已软删除的记录重新标记（Mark as Applied），会自动恢复该记录
   - 这样用户可以在不手动操作数据库的情况下恢复误删的记录

### 前端确认弹窗

- 移除了之前只对 critical statuses（applied, interviewing, offer）的确认逻辑
- 现在对所有取消操作都显示统一的确认弹窗：
  ```
  "Are you sure you want to clear the application status for this job?"
  ```
- 如果用户点击"取消"，不会发起任何 API 请求，也不会修改本地状态

## 手动测试步骤

### 1. 启动服务

```bash
# 启动后端（如果使用 Docker）
docker compose restart rag-api

# 或直接启动前端开发服务器
cd ui && npm run dev
```

### 2. 功能测试

1. **打开 JobHunter 页面**
   - 访问 `http://localhost:5173/jobhunter`（或你的前端地址）

2. **测试标记为 Applied**
   - 在左侧列表中选择一个 job
   - 点击 "Mark as Applied" 按钮
   - 确认状态标签变成 "Applied"

3. **测试取消标记（确认弹窗）**
   - 点击 "Unmark" 按钮
   - **验证点 1**: 浏览器应该弹出确认框："Are you sure you want to clear the application status for this job?"
   - 点击"取消"：状态应该保持不变（仍然是 "Applied"）
   - 再次点击 "Unmark"，这次点击"确认"
   - **验证点 2**: 状态应该消失，按钮变回 "Mark as Applied"

4. **测试软删除持久化**
   - 刷新页面（F5 或 Cmd+R）
   - **验证点 3**: 刚才 Unmark 的 job 应该仍然是未标记状态（说明软删除 + 前端状态同步都生效）
   - 数据库中该记录应该存在，但 `deleted = 1`

5. **测试 Application Tracker 视图（如果已实现）**
   - 打开 Application Tracker 视图
   - **验证点 4**: 确认里面看不到已软删除的那条记录

### 3. 数据库验证（可选）

如果需要直接验证数据库：

```bash
# 连接到 SQLite 数据库
sqlite3 .runs/jobhunter_cache.sqlite3

# 查看 job_applications 表结构（确认 deleted 字段存在）
.schema job_applications

# 查看所有记录（包括软删除的）
SELECT id, cache_id, status, deleted, last_updated_at FROM job_applications;

# 只查看未删除的记录
SELECT id, cache_id, status, deleted FROM job_applications WHERE deleted = 0;

# 只查看已软删除的记录
SELECT id, cache_id, status, deleted, last_updated_at FROM job_applications WHERE deleted = 1;
```

## 注意事项

1. **数据恢复**：如果需要恢复已软删除的记录，可以手动执行：
   ```sql
   UPDATE job_applications SET deleted = 0 WHERE id = ?;
   ```

2. **性能考虑**：所有查询都添加了 `deleted = 0` 条件，建议在 `deleted` 字段上创建索引（如果数据量很大）：
   ```sql
   CREATE INDEX IF NOT EXISTS idx_job_applications_deleted 
   ON job_applications(deleted);
   ```

3. **前端状态同步**：前端在成功删除后会立即从 `applicationStatusMap` 中移除该记录，确保 UI 即时更新。

## 验证清单

- [x] 后端代码编译通过（`python3 -m py_compile`）
- [x] 前端代码无 TypeScript 错误
- [x] 数据库迁移逻辑幂等（可多次调用）
- [x] 查询函数正确过滤软删除记录
- [x] 删除函数正确执行软删除
- [x] 前端确认弹窗对所有操作生效
- [x] 前端状态同步正确（删除后立即更新 UI）

## 后续优化建议

1. 考虑添加索引：在 `deleted` 字段上创建索引以提高查询性能
2. 考虑添加清理任务：定期清理很久以前软删除的记录（如果需要）
3. 考虑添加审计日志：记录谁在什么时候软删除了哪些记录（如果需要）

