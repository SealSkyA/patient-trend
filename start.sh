#!/bin/bash
# ============================================
# 「报告管理」APP — 一键启动脚本
# 自动检测配置、启动后端、启动前端
# 如果配置缺失会主动提示用户
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_ok()   { echo -e "${GREEN}[成功]${NC} $1"; }
log_err()  { echo -e "${RED}[错误]${NC} $1"; }
log_info() { echo -e "${YELLOW}[信息]${NC} $1"; }
log_step() { echo -e "\n${BLUE}--- $1 ---${NC}"; }

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "====================================="
echo "  「报告管理」APP"
echo "  一键启动"
echo "====================================="
echo ""

# -------------------------------------------
# 1. 检查后端配置
# -------------------------------------------
log_step "检查后端配置"

ENV_FILE="${PROJECT_ROOT}/.env"
if [ ! -f "$ENV_FILE" ]; then
    log_err "找不到 ${ENV_FILE}"
    log_info "请先运行: bash deploy/config.sh 完成配置"
    exit 1
fi

# 读取配置
DB_URL=$(grep "^DATABASE_URL" "$ENV_FILE" | cut -d'=' -f2- | head -1)
if [ -z "$DB_URL" ]; then
    log_err ".env 中未找到 DATABASE_URL"
    log_info "请编辑 ${ENV_FILE} 添加 DATABASE_URL"
    exit 1
fi

SECRET_KEY=$(grep "^SECRET_KEY" "$ENV_FILE" | cut -d'=' -f2- | head -1)
if [ -z "$SECRET_KEY" ]; then
    log_err ".env 中未找到 SECRET_KEY"
    log_info "请编辑 ${ENV_FILE} 添加 SECRET_KEY，或运行 bash deploy/config.sh 自动生成"
    exit 1
fi

log_ok "后端配置已就绪"

# -------------------------------------------
# 2. 检查数据库连接
# -------------------------------------------
log_step "检查数据库连接"

# 从 DATABASE_URL 提取主机信息 (mysql+aiomysql://user:pass@host:port/db)
DB_HOST=$(echo "$DB_URL" | sed -n 's|.*://[^@]*@\([^:]*\).*|\1|p')
DB_PORT=$(echo "$DB_URL" | sed -n 's|.*@\([^:]*\):\([0-9]*\)/.*|\2|p')
DB_PORT="${DB_PORT:-3306}"

if command -v mysqladmin &>/dev/null; then
    if mysqladmin ping -h "${DB_HOST:-localhost}" -P "${DB_PORT}" --silent 2>/dev/null; then
        log_ok "MySQL 服务运行正常 (${DB_HOST}:${DB_PORT})"
    else
        log_err "MySQL 连接失败 (${DB_HOST}:${DB_PORT})"
        log_info "尝试启动 MySQL: sudo systemctl start mysqld"
        sudo systemctl start mysqld 2>/dev/null && {
            sleep 2
            mysqladmin ping -h "${DB_HOST:-localhost}" -P "${DB_PORT}" --silent 2>/dev/null && log_ok "MySQL 启动成功" || {
                log_err "无法启动 MySQL，请手动排查"
                exit 1
            }
        } || {
            log_err "MySQL 服务未安装或未启动"
            exit 1
        }
    fi
else
    log_info "未找到 mysqladmin，跳过数据库连接检查"
fi

# -------------------------------------------
# 3. 安装依赖
# -------------------------------------------
log_step "检查并安装依赖"

# 后端
if [ -f "${PROJECT_ROOT}/backend/requirements.txt" ]; then
    if python3.11 -c "import fastapi" 2>/dev/null; then
        log_ok "后端 Python 依赖已就绪"
    else
        log_info "安装后端依赖..."
        python3.11 -m pip install -r "${PROJECT_ROOT}/backend/requirements.txt" --break-system-packages 2>&1 | tail -1 || \
        python3.11 -m pip install -r "${PROJECT_ROOT}/backend/requirements.txt" 2>&1 | tail -1
        if python3.11 -c "import fastapi" 2>/dev/null; then
            log_ok "后端依赖安装完成"
        else
            log_err "后端依赖安装失败"
            exit 1
        fi
    fi
fi

# 前端
if [ -f "${PROJECT_ROOT}/frontend/package.json" ]; then
    if [ -f "${PROJECT_ROOT}/frontend/node_modules/.package-lock.json" ]; then
        log_ok "前端 Node.js 依赖已就绪"
    else
        log_info "安装前端依赖..."
        cd "${PROJECT_ROOT}/frontend"
        npm install 2>&1 | tail -1 || {
            log_info "npm install 失败，切换淘宝镜像..."
            npm config set registry https://registry.npmmirror.com
            npm install 2>&1 | tail -1
        }
        if [ $? -eq 0 ]; then
            log_ok "前端依赖安装完成"
        else
            log_err "前端依赖安装失败"
            exit 1
        fi
    fi
fi

# -------------------------------------------
# 4. 停止旧进程
# -------------------------------------------
log_step "清理旧进程"

pkill -f "uvicorn.*backend.main:app" 2>/dev/null && log_info "已停止旧后端进程" || log_info "无旧后端进程"
pkill -f "npm run dev.*35000" 2>/dev/null && log_info "已停止旧前端进程" || log_info "无旧前端进程"
sleep 1

# -------------------------------------------
# 5. 启动后端
# -------------------------------------------
log_step "启动后端 (端口 35001)"

cd "${PROJECT_ROOT}"

# 创建日志目录
mkdir -p "${PROJECT_ROOT}/logs"

nohup python3.11 -m uvicorn backend.main:app \
    --host 0.0.0.0 --port 35001 \
    --reload \
    > "${PROJECT_ROOT}/logs/backend.log" 2>&1 &
BACKEND_PID=$!

# 等待后端就绪
log_info "等待后端启动..."
for i in $(seq 1 30); do
    if curl -s http://localhost:35001/api/health &>/dev/null; then
        log_ok "后端启动成功 (PID: $BACKEND_PID)"
        break
    fi
    if [ $i -eq 30 ]; then
        log_err "后端启动超时 (${i}秒)"
        log_info "查看日志: cat ${PROJECT_ROOT}/logs/backend.log"
        exit 1
    fi
    sleep 1
done

# -------------------------------------------
# 6. 启动前端
# -------------------------------------------
log_step "启动前端 (端口 35000)"

cd "${PROJECT_ROOT}/frontend"

# 检查 .env.production 是否存在
PROD_ENV="${PROJECT_ROOT}/frontend/.env.production"
if [ ! -f "$PROD_ENV" ]; then
    log_info "创建默认 .env.production..."
    echo "VITE_API_BASE_URL=http://localhost:35001" > "$PROD_ENV"
fi

nohup npm run dev -- --host 0.0.0.0 --port 35000 \
    > "${PROJECT_ROOT}/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

log_info "等待前端启动..."
sleep 5
if curl -s http://localhost:35000 &>/dev/null; then
    log_ok "前端启动成功 (PID: $FRONTEND_PID)"
else
    log_info "前端还在加载中，请稍候访问..."
fi

# -------------------------------------------
# 7. 汇总
# -------------------------------------------
echo ""
echo "====================================="
echo -e "  ${GREEN}服务全部启动!${NC}"
echo "====================================="
echo -e "  前端: ${BLUE}http://localhost:35000${NC}"
echo -e "  后端: ${BLUE}http://localhost:35001/api/docs${NC}"
echo -e "  健康: ${BLUE}http://localhost:35001/api/health${NC}"
echo "====================================="
echo ""
echo -e "后端日志: ${YELLOW}tail -f ${PROJECT_ROOT}/logs/backend.log${NC}"
echo -e "前端日志: ${YELLOW}tail -f ${PROJECT_ROOT}/logs/frontend.log${NC}"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    pkill -f "uvicorn.*backend.main:app" 2>/dev/null
    pkill -f "npm run dev.*35000" 2>/dev/null
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

trap cleanup INT TERM

wait
