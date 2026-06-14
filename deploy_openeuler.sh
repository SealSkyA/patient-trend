#!/bin/bash
# 部署脚本 for OpenEuler 22.03 SP1

set -e

echo "[1/6] 安装 Node.js 和 Python..."
sudo dnf install -y nodejs npm python3.11 python3.11-pip gcc make

echo "[2/6] 配置 MySQL 数据库..."
echo "请输入 MySQL root 密码:"
read -s DB_ROOT_PASS
mysql -u root -p"$DB_ROOT_PASS" -e "CREATE DATABASE IF NOT EXISTS patient_trend DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p"$DB_ROOT_PASS" -e "CREATE USER IF NOT EXISTS 'patient_user'@'localhost' IDENTIFIED BY 'PatientTrendPass2026!';"
mysql -u root -p"$DB_ROOT_PASS" -e "GRANT ALL PRIVILEGES ON patient_trend.* TO 'patient_user'@'localhost';"
mysql -u root -p"$DB_ROOT_PASS" -e "FLUSH PRIVILEGES;"

echo "[3/6] 配置后端环境变量..."
cat > backend/.env << EOF
DATABASE_URL=mysql+aiomysql://patient_user:PatientTrendPass2026!@localhost:3306/patient_trend?charset=utf8mb4
DATABASE_ECHO=false
SECRET_KEY=$(openssl rand -hex 32)
ACCESS_TOKEN_EXPIRE_MINUTES=10080
DEBUG=true
EOF

echo "[4/6] 安装后端依赖..."
pip3.11 install -r backend/requirements.txt --break-system-packages 2>/dev/null || pip3 install -r backend/requirements.txt

echo "[5/6] 安装前端依赖..."
cd frontend && npm install && cd ..
npm run build --prefix frontend

echo "[6/6] 启动服务..."
echo "启动后端 (端口 35001)..."
nohup pip3.11 run uvicorn backend.main:app --host 0.0.0.0 --port 35001 > backend.log 2>&1 &
echo $! > backend.pid

sleep 3

echo "服务已启动!"
echo "前端构建在 frontend/dist/"
echo "请使用 Nginx 托管 frontend/dist 并反向代理 /api 到 35001"
