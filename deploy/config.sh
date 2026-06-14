#!/bin/bash
# ============================================
# 「报告管理」APP — 配置脚本
# 交互式引导用户填写数据库信息、密钥、后端地址
# 自动创建数据库、生成 .env 文件
# ============================================

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_ok()   { echo -e "${GREEN}[成功]${NC} $1"; }
log_err()  { echo -e "${RED}[错误]${NC} $1"; }
log_info() { echo -e "${YELLOW}[信息]${NC} $1"; }
log_q()    { echo -e "${BLUE}[配置]${NC} $1"; }

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "====================================="
echo "  「报告管理」APP — 项目配置"
echo "====================================="
echo ""
echo -e "${YELLOW}请根据实际情况填写以下配置项${NC}"
echo ""

# -------------------------------------------
# 1. 数据库配置
# -------------------------------------------
echo "--- 1. MySQL 数据库配置 ---"
echo ""

# MySQL root 密码
echo "请提供 MySQL root 用户密码（安装 MySQL 时设置的密码）"
echo "如果是首次安装且没有设置密码，直接回车即可"
read -p "MySQL root 密码 [留空=无密码]: " MYSQL_ROOT_PW

# 测试连接
log_info "测试 MySQL root 连接..."
if mysql -u root -p"${MYSQL_ROOT_PW:-}" -e "SELECT 1;" &>/dev/null; then
    log_ok "MySQL root 连接成功"
else
    # 尝试 socket 方式
    if mysql -u root -e "SELECT 1;" &>/dev/null; then
        log_ok "MySQL socket 连接成功（无密码）"
        MYSQL_ROOT_PW=""
    else
        log_err "无法连接 MySQL，请检查密码或服务状态"
        log_info "排查: sudo systemctl status mysqld"
        exit 1
    fi
fi

# 数据库名
echo ""
read -p "数据库名称 [patient_trend]: " DB_NAME
DB_NAME="${DB_NAME:-patient_trend}"

# 数据库用户
read -p "数据库用户名 [patient_user]: " DB_USER
DB_USER="${DB_USER:-patient_user}"

# 数据库密码（必须填写）
echo ""
echo "请为 ${DB_USER} 设置一个密码（至少 8 位，建议包含大小写和数字）"
while true; do
    read -sp "数据库密码: " DB_PW
    echo ""
    if [ ${#DB_PW} -lt 8 ]; then
        log_err "密码太短（至少 8 位），请重新输入"
        continue
    fi
    read -sp "确认密码: " DB_PW2
    echo ""
    if [ "$DB_PW" != "$DB_PW2" ]; then
        log_err "两次输入的密码不一致，请重新输入"
        continue
    fi
    break
done

# 数据库主机
echo ""
read -p "MySQL 服务器地址 [localhost:3306] (一般保持默认): " DB_HOST_PORT
DB_HOST_PORT="${DB_HOST_PORT:-localhost:3306}"
DB_HOST="${DB_HOST_PORT%%:*}"
DB_PORT="${DB_HOST_PORT#*:}"
DB_PORT="${DB_PORT:-3306}"

# -------------------------------------------
# 2. 创建数据库和用户
# -------------------------------------------
echo ""
echo "--- 创建数据库和用户 ---"

log_info "创建数据库 ${DB_NAME}..."
mysql -u root -p"${MYSQL_ROOT_PW:-}" -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
    log_err "创建数据库失败"
    exit 1
}
log_ok "数据库 ${DB_NAME} 已就绪"

log_info "创建用户 ${DB_USER}..."
mysql -u root -p"${MYSQL_ROOT_PW:-}" -e "
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PW}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;" 2>/dev/null || {
    log_err "创建用户失败"
    exit 1
}
log_ok "用户 ${DB_USER} 已就绪"

# 验证
log_info "验证数据库连接..."
if mysql -u "${DB_USER}" -p"${DB_PW}" "${DB_NAME}" -e "SELECT 'OK' as status;" 2>/dev/null | grep -q "OK"; then
    log_ok "数据库连接验证通过"
else
    log_err "数据库连接验证失败"
    exit 1
fi

# -------------------------------------------
# 3. 后端 .env 配置
# -------------------------------------------
echo ""
echo "--- 3. 后端配置文件 ---"

# 生成 SECRET_KEY
log_info "生成 JWT 密钥..."
if check_cmd openssl || command -v openssl &>/dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
    log_ok "SECRET_KEY 已生成"
else
    # 备选: 用 python 生成
    SECRET_KEY=$(python3.11 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || \
                 python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null)
    if [ -n "$SECRET_KEY" ]; then
        log_ok "SECRET_KEY 已生成 (python)"
    else
        # 最终方案: 随机字符串
        SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -1)
        log_ok "SECRET_KEY 已生成 (随机)"
    fi
fi

# 创建后端 .env
ENV_PATH="${PROJECT_ROOT}/.env"
log_info "写入后端配置: ${ENV_PATH}"

cat > "${ENV_PATH}" << EOF
DATABASE_URL=mysql+aiomysql://${DB_USER}:${DB_PW}@${DB_HOST}:${DB_PORT}/${DB_NAME}?charset=utf8mb4
DATABASE_ECHO=false

# JWT 密钥（自动生成，不要修改）
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 生产环境请设为 false
DEBUG=false
EOF

log_ok "后端配置写入完成"

# -------------------------------------------
# 4. 前端 API 地址配置
# -------------------------------------------
echo ""
echo "--- 4. 前端 API 地址配置 ---"

echo ""
echo "APP 需要知道后端 API 的地址，请根据你的情况选择："
echo "  1) 本机部署（前端和后端在同一台机器上）"
echo "  2) 远程部署（后端在云服务器上，需要公网 IP/域名）"
echo ""
read -p "请选择 [1/2] (默认=1): " DEPLOY_TYPE
DEPLOY_TYPE="${DEPLOY_TYPE:-1}"

if [ "$DEPLOY_TYPE" = "2" ]; then
    echo ""
    echo "请提供后端服务器的公网 IP 或域名"
    echo "例如: www.021897.xyz 或 123.45.67.89"
    while true; do
        read -p "后端服务器地址: " SERVER_ADDR
        if [ -z "$SERVER_ADDR" ]; then
            log_err "地址不能为空"
            continue
        fi
        break
    done

    read -p "后端端口 [35001]: " BACKEND_PORT
    BACKEND_PORT="${BACKEND_PORT:-35001}"
    BACKEND_URL="http://${SERVER_ADDR}:${BACKEND_PORT}"
else
    BACKEND_URL="http://localhost:35001"
fi

# 创建 .env.production
PROD_ENV="${PROJECT_ROOT}/frontend/.env.production"
log_info "写入前端配置: ${PROD_ENV}"

cat > "${PROD_ENV}" << EOF
# 生产环境配置（APP/公网访问）
VITE_API_BASE_URL=${BACKEND_URL}
EOF

log_ok "前端配置写入完成"

# 开发环境的配置也用本地代理
DEV_ENV="${PROJECT_ROOT}/frontend/.env.development"
cat > "${DEV_ENV}" << EOF
# 开发环境配置
VITE_API_BASE_URL=/api

# 开发服务器代理
VITE_SERVER_URL=http://localhost:35001
EOF
log_ok "开发环境配置写入完成"

# -------------------------------------------
# 5. 防火墙配置
# -------------------------------------------
echo ""
echo "--- 5. 防火墙配置 ---"

if check_cmd firewall-cmd; then
    echo "检测到 firewalld，是否开放端口? [y/n] (默认=y)"
    read -p "是否开放 35000/35001 端口: " FIREWALL_YN
    FIREWALL_YN="${FIREWALL_YN:-y}"
    
    if [ "$FIREWALL_YN" = "y" ] || [ "$FIREWALL_YN" = "Y" ]; then
        log_info "开放端口 35000 (前端) 和 35001 (后端)..."
        sudo firewall-cmd --permanent --add-port=35000/tcp 2>/dev/null || log_err "开放 35000 端口失败"
        sudo firewall-cmd --permanent --add-port=35001/tcp 2>/dev/null || log_err "开放 35001 端口失败"
        sudo firewall-cmd --reload 2>/dev/null || log_err "重载防火墙失败"
        log_ok "端口已开放"
    fi
elif check_cmd ufw; then
    echo "检测到 ufw，是否开放端口? [y/n] (默认=y)"
    read -p "是否开放 35000/35001 端口: " FIREWALL_YN
    FIREWALL_YN="${FIREWALL_YN:-y}"
    
    if [ "$FIREWALL_YN" = "y" ] || [ "$FIREWALL_YN" = "Y" ]; then
        log_info "开放端口..."
        sudo ufw allow 35000/tcp 2>/dev/null || log_err "开放 35000 端口失败"
        sudo ufw allow 35001/tcp 2>/dev/null || log_err "开放 35001 端口失败"
        log_ok "端口已开放"
    fi
else
    log_info "未检测到防火墙，跳过端口开放"
    log_info "如果启用了其他防火墙，请手动开放 35000 和 35001 端口"
fi

# -------------------------------------------
# 6. 最终确认
# -------------------------------------------
echo ""
echo "====================================="
echo "  配置完成!"
echo "====================================="
echo ""
echo -e "数据库: ${GREEN}${DB_NAME}${NC} (用户: ${DB_USER})"
echo -e "后端 API: ${GREEN}${BACKEND_URL}${NC}"
echo -e "后端配置: ${GREEN}${ENV_PATH}${NC}"
echo -e "前端配置: ${GREEN}${PROD_ENV}${NC}"
echo ""
echo "下一步: 启动服务"
echo -e "  ${BLUE}cd ${PROJECT_ROOT}${NC}"
echo -e "  ${BLUE}bash start.sh${NC}"
echo ""
echo "如需修改配置，直接编辑对应 .env 文件后重启服务即可"
