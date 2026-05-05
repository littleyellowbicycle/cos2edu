#!/bin/bash

set -e

echo "=========================================="
echo "  苏格拉底AI教学系统 - 启动脚本"
echo "=========================================="
echo "环境: ${APP_ENV:-prod}"
echo "时间: $(date)"
echo ""

echo "[1/4] 检查数据目录..."
DATA_DIR="./data"
mkdir -p "${DATA_DIR}/characters"
mkdir -p "${DATA_DIR}/materials"
mkdir -p "${DATA_DIR}/conversations"
mkdir -p "${DATA_DIR}/uploads/avatars"
mkdir -p "${DATA_DIR}/uploads/backgrounds"

if [ ! -w "$DATA_DIR" ]; then
    echo "⚠ 警告: 数据目录不可写，上传功能可能无法正常工作"
    echo "  请确保主机目录权限正确或使用命名卷"
fi
echo "✓ 数据目录已就绪"

echo ""
echo "[2/4] 运行数据库迁移..."
if [ -f "migrate_db.py" ]; then
    python migrate_db.py
    echo "✓ 数据库迁移完成"
else
    echo "⚠ 未找到 migrate_db.py，跳过迁移"
fi

echo ""
echo "[3/4] 初始化数据（首次运行）..."
if [ -f "init_data.py" ]; then
    python init_data.py
    echo "✓ 数据初始化完成"
else
    echo "⚠ 未找到 init_data.py，跳过初始化"
fi

echo ""
echo "=========================================="
echo "  启动应用服务..."
echo "=========================================="
echo "访问地址: http://localhost:${APP_PORT:-8000}"
echo "健康检查: http://localhost:${APP_PORT:-8000}/health"
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000
