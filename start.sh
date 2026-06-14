#!/bin/bash

# ============================================
# 患者检查报告趋势分析系统 - 启动脚本
# ============================================

echo "====================================="
echo "  患者检查报告趋势分析系统"
echo "====================================="
echo ""

# 检查 MySQL 是否运行
if ! mysqladmin ping -h localhost --silent 2>/dev/null; then
    echo "[错误] MySQL 未运行，请先启动 MySQL"
    exit 1
fi

# 检查数据库是否存在
DB_EXISTS=$(mysql -u root -e "SHOW DATABASES LIKE 'patient_trend';" 2>/dev/null | grep -c patient_trend)
if [ "$DB_EXISTS" -eq 0 ]; then
    echo "[信息] 创建数据库 patient_trend..."
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS patient_trend DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    echo "[成功] 数据库创建完成"
fi

# 启动后端
echo ""
echo "[信息] 启动后端服务 (端口 35001)..."
cd "$(dirname "$0")/backend"
nohup uvicorn main:app --host 0.0.0.0 --port 35001 > backend.log 2>&1 &
BACKEND_PID=$!
echo "[成功] 后端启动完成 (PID: $BACKEND_PID)"

# 等待后端就绪
echo "[信息] 等待后端就绪..."
sleep 3

# 启动前端
echo "[信息] 启动前端服务 (端口 35000)..."
cd "$(dirname "$0")/frontend"
nohup npm run dev -- --port 35000 --host 0.0.0.0 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "[成功] 前端启动完成 (PID: $FRONTEND_PID)"

echo ""
echo "====================================="
echo "  服务启动完成"
echo "====================================="
echo "  前端: http://localhost:35000"
echo "  后端: http://localhost:35001"
echo "  后文档: http://localhost:35001/api/docs"
echo "====================================="
echo ""
echo "后端日志: tail -f backend/backend.log"
echo "前端日志: tail -f frontend/frontend.log"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 清理
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '服务已停止'; exit" INT TERM
wait
