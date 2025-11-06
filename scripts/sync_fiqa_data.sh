#!/bin/bash
# 同步整个 data/fiqa_v1/ 目录到 RTX3080 服务器
# 使用方法: ./scripts/sync_fiqa_data.sh

set -e

REMOTE="andy-wsl"
REMOTE_DIR="~/searchforge"
LOCAL_DATA_DIR="data/fiqa_v1"
REMOTE_DATA_DIR="data/fiqa_v1"

PROJECT_ROOT="/Users/nanxinli/Documents/dev/searchforge"

echo "🔄 同步 data/fiqa_v1/ 目录到 RTX3080..."
echo ""

# 检查本地目录是否存在
if [ ! -d "$PROJECT_ROOT/$LOCAL_DATA_DIR" ]; then
    echo "❌ 错误: 本地目录不存在: $PROJECT_ROOT/$LOCAL_DATA_DIR"
    exit 1
fi

# 显示要同步的内容
echo "📦 本地目录内容:"
ls -lh "$PROJECT_ROOT/$LOCAL_DATA_DIR" | head -10
echo ""

# 计算大小
LOCAL_SIZE=$(du -sh "$PROJECT_ROOT/$LOCAL_DATA_DIR" | cut -f1)
echo "📊 目录大小: $LOCAL_SIZE"
echo ""

# 确认
read -p "确认同步到 $REMOTE:$REMOTE_DIR/$REMOTE_DATA_DIR ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消同步"
    exit 1
fi

# 使用 rsync 同步（保留权限和时间戳，显示进度）
echo "🚀 开始同步..."
rsync -avz --progress \
    "$PROJECT_ROOT/$LOCAL_DATA_DIR/" \
    "$REMOTE:$REMOTE_DIR/$REMOTE_DATA_DIR/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 同步完成！"
    echo ""
    
    # 验证远程文件
    echo "🔍 验证远程文件..."
    ssh "$REMOTE" "cd $REMOTE_DIR && ls -lh $REMOTE_DATA_DIR/ | head -10"
    echo ""
    
    # 检查关键文件
    echo "📋 检查关键文件..."
    ssh "$REMOTE" "cd $REMOTE_DIR && \
        echo 'fiqa_50k_v1/corpus.jsonl:' && \
        (ls -lh $REMOTE_DATA_DIR/fiqa_50k_v1/corpus.jsonl 2>&1 || echo '  ❌ 不存在（可能需要创建链接到 corpus_50k_v1.jsonl）') && \
        echo 'fiqa_10k_v1/corpus.jsonl:' && \
        (ls -lh $REMOTE_DATA_DIR/fiqa_10k_v1/corpus.jsonl 2>&1 || echo '  ❌ 不存在（可能需要创建链接到 corpus_10k_v1.jsonl）') && \
        echo 'fiqa_50k_v1/queries.jsonl:' && \
        (ls -lh $REMOTE_DATA_DIR/fiqa_50k_v1/queries.jsonl 2>&1 || echo '  ❌ 不存在') && \
        echo 'corpus_50k_v1.jsonl (根目录):' && \
        ls -lh $REMOTE_DATA_DIR/corpus_50k_v1.jsonl 2>&1 || echo '  ❌ 不存在'"
    
    echo ""
    echo "🔗 创建符号链接（如果 corpus.jsonl 不在子目录中）..."
    # 创建符号链接，如果不存在的话
    ssh "$REMOTE" "cd $REMOTE_DIR && \
        if [ ! -f $REMOTE_DATA_DIR/fiqa_50k_v1/corpus.jsonl ] && [ -f $REMOTE_DATA_DIR/corpus_50k_v1.jsonl ]; then
            ln -sf ../corpus_50k_v1.jsonl $REMOTE_DATA_DIR/fiqa_50k_v1/corpus.jsonl && \
            echo '  ✅ 创建了 fiqa_50k_v1/corpus.jsonl -> ../corpus_50k_v1.jsonl'
        else
            echo '  ℹ️  fiqa_50k_v1/corpus.jsonl 已存在或源文件不存在'
        fi && \
        if [ ! -f $REMOTE_DATA_DIR/fiqa_10k_v1/corpus.jsonl ] && [ -f $REMOTE_DATA_DIR/corpus_10k_v1.jsonl ]; then
            ln -sf ../corpus_10k_v1.jsonl $REMOTE_DATA_DIR/fiqa_10k_v1/corpus.jsonl && \
            echo '  ✅ 创建了 fiqa_10k_v1/corpus.jsonl -> ../corpus_10k_v1.jsonl'
        else
            echo '  ℹ️  fiqa_10k_v1/corpus.jsonl 已存在或源文件不存在'
        fi"
    
    echo ""
    echo "💡 提示: 文件已同步，但 Docker 容器需要重启才能看到新文件（如果使用 volume 挂载）"
    echo "   执行: ssh $REMOTE 'cd $REMOTE_DIR && docker compose restart rag-api'"
else
    echo ""
    echo "❌ 同步失败"
    exit 1
fi

