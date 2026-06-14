#!/bin/bash
# ============================================
# 「报告管理」APP — 环境安装脚本
# 自动安装 Python 3.11, Node.js, MySQL, Git
# 每种软件都有多种安装方案，方案A失败自动切换方案B
# ============================================

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERROR_COUNT=0

echo "====================================="
echo "  「报告管理」APP — 环境安装"
echo "====================================="
echo ""

# -------------------------------------------
# 工具函数
# -------------------------------------------
log_ok()  { echo -e "${GREEN}[成功]${NC} $1"; }
log_err() { echo -e "${RED}[失败]${NC} $1"; ERROR_COUNT=$((ERROR_COUNT+1)); }
log_info() { echo -e "${YELLOW}[信息]${NC} $1"; }

check_cmd() { command -v "$1" &>/dev/null; }

# 检测 Linux 发行版
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME=$ID
        OS_VER=$VERSION_ID
    elif check_cmd rpm; then
        OS_NAME="rpm-based"
    else
        OS_NAME="unknown"
    fi
    log_info "检测到系统: $OS_NAME (版本 $OS_VER)"
}

# 检查是否 root 或有 sudo
check_root() {
    if [ "$(id -u)" -ne 0 ] && ! check_cmd sudo; then
        echo -e "${RED}[错误]${NC} 请以 root 用户运行，或安装 sudo"
        exit 1
    fi
    SUDO=""
    if [ "$(id -u)" -ne 0 ]; then
        SUDO="sudo"
    fi
}

# 重试函数: run_or_fallback "命令" "失败提示" "备选命令"
try_install() {
    local primary_cmd="$1"
    local primary_msg="$2"
    local fallback_cmd="$3"
    local fallback_msg="$4"
    local check_fn="$5"
    
    log_info "尝试: $primary_msg"
    if eval "$primary_cmd"; then
        if eval "$check_fn" 2>/dev/null; then
            log_ok "$primary_msg"
            return 0
        fi
    fi
    
    if [ -n "$fallback_cmd" ]; then
        log_info "方案A失败，尝试: $fallback_msg"
        if eval "$fallback_cmd"; then
            if eval "$check_fn" 2>/dev/null; then
                log_ok "$fallback_msg"
                return 0
            fi
        fi
    fi
    
    log_err "方案A 和方案B 都失败了: $primary_msg / $fallback_msg"
    return 1
}

# -------------------------------------------
# 1. 检测系统
# -------------------------------------------
detect_os
check_root

# -------------------------------------------
# 2. 安装 Git
# -------------------------------------------
echo ""
echo "----- 安装 Git -----"

if check_cmd git; then
    log_ok "Git 已安装: $(git --version)"
else
    # 方案A: dnf
    try_install \
        "$SUDO dnf install -y git" "dnf install git" \
        "$SUDO apt install -y git" "apt install git" \
        "git --version"
    
    if ! check_cmd git; then
        # 方案C: 源码编译
        log_info "方案C: 从源码编译 Git..."
        $SUDO apt install -y build-essential libcurl4-openssl-dev libssl-dev zlib1g-dev 2>/dev/null || true
        cd /tmp
        curl -LO https://github.com/git/git/archive/v2.43.0.tar.gz 2>/dev/null || {
            log_err "下载 Git 源码失败"
            exit 1
        }
        tar -xzf v2.43.0.tar.gz && cd git-2.43.0
        make prefix=/usr/local all -j$(nproc) && $SUDO make prefix=/usr/local install
        cd /
    fi
    
    if check_cmd git; then
        log_ok "Git 安装完成: $(git --version)"
    else
        log_err "Git 安装失败，请手动安装后重试"
        exit 1
    fi
fi

# -------------------------------------------
# 3. 安装 Python 3.11
# -------------------------------------------
echo ""
echo "----- 安装 Python 3.11 -----"

PYTHON311=""
if check_cmd python3.11; then
    PYTHON311="python3.11"
    log_ok "Python 3.11 已安装: $(python3.11 --version)"
elif check_cmd python311; then
    PYTHON311="python311"
    log_ok "Python 3.11 已安装 (python311): $(python311 --version)"
fi

if [ -z "$PYTHON311" ]; then
    log_info "方案A: dnf 安装 Python 3.11..."
    if eval "$SUDO dnf install -y python3.11 python3.11-pip python3.11-devel" 2>/dev/null; then
        PYTHON311="python3.11"
    else
        # openEuler 22.03 有时包名不同
        if eval "$SUDO dnf install -y python311 python311-pip python311-devel" 2>/dev/null; then
            PYTHON311="python311"
        fi
    fi

    if [ -z "$PYTHON311" ] || ! check_cmd "$PYTHON311"; then
        log_info "方案A 失败，尝试: apt install python3.11..."
        if eval "$SUDO apt install -y python3.11 python3.11-venv python3.11-dev" 2>/dev/null; then
            PYTHON311="python3.11"
        fi
    fi

    if [ -z "$PYTHON311" ] || ! check_cmd "$PYTHON311"; then
        log_info "方案A/B 都失败，尝试方案C: deadsnakes PPA (Ubuntu/Debian)..."
        if eval "$SUDO apt install -y software-properties-common" 2>/dev/null; then
            eval "$SUDO add-apt-repository -y ppa:deadsnakes/ppa" 2>/dev/null || true
            if eval "$SUDO apt install -y python3.11 python3.11-venv python3.11-dev" 2>/dev/null; then
                PYTHON311="python3.11"
            fi
        fi
    fi

    if [ -z "$PYTHON311" ] || ! check_cmd "$PYTHON311"; then
        log_info "方案A/B/C 都失败，尝试方案D: 从源码编译 Python 3.11..."
        $SUDO dnf install -y gcc gcc-c++ make zlib-devel bzip2-devel \
            openssl-devel ncurses-devel sqlite-devel readline-devel \
            tk-devel gdbm-devel db4-devel libpcap-devel xz-devel libffi-devel 2>/dev/null || true
        $SUDO apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
            libssl-dev libsqlite3-dev libreadline-dev libbz2-dev libffi-dev wget 2>/dev/null || true
        
        cd /tmp
        curl -O https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz 2>/dev/null || {
            log_err "下载 Python 源码失败"
            exit 1
        }
        tar -xzf Python-3.11.9.tgz
        cd Python-3.11.9
        ./configure --enable-optimizations --prefix=/usr/local 2>&1 | tail -1
        make -j$(nproc) 2>&1 | tail -1
        $SUDO make altinstall 2>&1 | tail -1
        cd /
        PYTHON311="python3.11"
    fi

    if check_cmd python3.11; then
        PYTHON311="python3.11"
        log_ok "Python 3.11 安装完成: $(python3.11 --version)"
    elif check_cmd python311; then
        PYTHON311="python311"
        log_ok "Python 3.11 安装完成: $(python311 --version)"
    else
        log_err "Python 3.11 所有安装方案均失败"
        log_info "请手动安装，参考: https://www.python.org/downloads/"
        exit 1
    fi
fi

# 安装 pip 依赖
log_info "安装 Python 依赖 (backend/requirements.txt)..."
cd "$(dirname "$0")/workspace"
if [ -f backend/requirements.txt ]; then
    # 尝试正常 pip install
    if $PYTHON311 -m pip install -r backend/requirements.txt --break-system-packages 2>&1 | tail -5; then
        log_ok "Python 依赖安装完成"
    else
        # 备选: 不用 --break-system-packages
        log_info "方案A 失败，尝试不用 --break-system-packages..."
        if $PYTHON311 -m pip install -r backend/requirements.txt 2>&1 | tail -5; then
            log_ok "Python 依赖安装完成"
        else
            log_err "Python 依赖安装失败，请查看上方错误信息"
        fi
    fi
else
    log_err "找不到 backend/requirements.txt，请确认当前目录正确"
fi

cd "$(dirname "$0")"

# -------------------------------------------
# 4. 安装 Node.js
# -------------------------------------------
echo ""
echo "----- 安装 Node.js -----"

if check_cmd node; then
    NODEVER=$(node -v | grep -oP '\d+' | head -1)
    if [ "$NODEVER" -ge 18 ] 2>/dev/null; then
        log_ok "Node.js 已安装: $(node -v)"
    else
        log_info "Node 版本过低 ($NODEVER)，需要 >= 18"
        NEED_NODE=1
    fi
else
    NEED_NODE=1
fi

if [ "${NEED_NODE:-0}" -eq 1 ]; then
    # 方案A: nodesource
    log_info "方案A: nodesource 安装 Node.js 20..."
    if curl -fsSL https://rpm.nodesource.com/setup_20.x 2>/dev/null | $SUDO bash - 2>/dev/null; then
        $SUDO dnf install -y nodejs 2>/dev/null || true
    elif curl -fsSL https://deb.nodesource.com/setup_20.x 2>/dev/null | $SUDO bash - 2>/dev/null; then
        $SUDO apt install -y nodejs 2>/dev/null || true
    fi

    if ! check_cmd node || [ "$(node -v | grep -oP '\d+' | head -1)" -lt 18 ] 2>/dev/null; then
        # 方案B: nvm
        log_info "方案A 失败，尝试方案B: nvm..."
        export NVM_DIR="$HOME/.nvm"
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh 2>/dev/null | bash
        [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
        nvm install 20 2>/dev/null || true
        nvm use 20 2>/dev/null || true
    fi

    if ! check_cmd node || [ "$(node -v | grep -oP '\d+' | head -1)" -lt 18 ] 2>/dev/null; then
        # 方案C: 直接下载二进制
        log_info "方案A/B 失败，尝试方案C: 下载预编译 Node.js..."
        ARCH=$(uname -m)
        if [ "$ARCH" = "x86_64" ]; then
            NODE_URL="https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.xz"
        elif [ "$ARCH" = "aarch64" ]; then
            NODE_URL="https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-arm64.tar.xz"
        else
            log_err "不支持的架构: $ARCH"
        fi
        
        if [ -n "${NODE_URL:-}" ]; then
            cd /tmp
            curl -LO "$NODE_URL" 2>/dev/null || {
                log_err "下载 Node.js 二进制失败"
                exit 1
            }
            tar -xf node-v20.18.0-linux-*.tar.xz
            $SUDO cp -r node-v20.18.0-linux-*/bin/* /usr/local/bin/
            $SUDO cp -r node-v20.18.0-linux-*/lib/* /usr/local/lib/
            $SUDO cp -r node-v20.18.0-linux-*/include/* /usr/local/include/
            cd /
        fi
    fi

    if check_cmd node; then
        log_ok "Node.js 安装完成: $(node -v) $(npm -v)"
    else
        log_err "Node.js 所有安装方案均失败"
        exit 1
    fi
fi

# 安装前端依赖
log_info "安装前端依赖 (frontend/package.json)..."
if [ -f frontend/package.json ]; then
    # 尝试默认镜像
    if npm install 2>&1 | tail -5; then
        log_ok "前端依赖安装完成"
    else
        log_info "方案A 失败，切换到淘宝镜像..."
        npm config set registry https://registry.npmmirror.com
        if npm install 2>&1 | tail -5; then
            log_ok "前端依赖安装完成 (淘宝镜像)"
        else
            log_err "前端依赖安装失败，请查看上方错误信息"
        fi
    fi
else
    log_err "找不到 frontend/package.json"
fi

# -------------------------------------------
# 5. 安装 MySQL
# -------------------------------------------
echo ""
echo "----- 安装/配置 MySQL -----"

MYSQL_INSTALLED=0
if check_cmd mysql; then
    if mysqladmin ping -h localhost --silent 2>/dev/null; then
        log_ok "MySQL 已安装并运行"
        MYSQL_INSTALLED=1
    else
        log_info "MySQL 客户端存在，但服务未运行"
    fi
fi

if [ "$MYSQL_INSTALLED" -eq 0 ]; then
    # 方案A: dnf
    log_info "方案A: dnf 安装 MySQL Server..."
    if $SUDO dnf install -y mysql-server 2>/dev/null; then
        log_ok "MySQL Server 安装完成 (dnf)"
    # 方案B: apt
    elif $SUDO apt install -y mysql-server 2>/dev/null; then
        log_ok "MySQL Server 安装完成 (apt)"
    # 方案C: 尝试 mariadb
    else
        log_info "MySQL 安装失败，尝试 MariaDB..."
        if $SUDO dnf install -y mariadb-server 2>/dev/null || $SUDO apt install -y mariadb-server 2>/dev/null; then
            log_ok "MariaDB 安装完成 (作为 MySQL 替代品)"
        else
            log_err "MySQL/MariaDB 所有方案均失败"
            log_info "请手动安装 MySQL 或 MariaDB"
        fi
    fi

    # 启动 MySQL 服务
    if check_cmd mysqld || check_cmd mariadbd; then
        log_info "启动数据库服务..."
        $SUDO systemctl start mysqld 2>/dev/null || \
        $SUDO systemctl start mariadb 2>/dev/null || \
        $SUDO systemctl start mysql 2>/dev/null || {
            log_err "无法启动数据库服务，请手动启动"
            exit 1
        }
        $SUDO systemctl enable mysqld 2>/dev/null || \
        $SUDO systemctl enable mariadb 2>/dev/null || true
        
        if mysqladmin ping -h localhost --silent 2>/dev/null; then
            log_ok "数据库服务已启动"
        fi
    fi
fi

# -------------------------------------------
# 6. 汇总
# -------------------------------------------
echo ""
echo "====================================="
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}环境安装全部完成!${NC}"
else
    echo -e "  ${RED}有 $ERROR_COUNT 项安装失败，请查看上方错误信息${NC}"
fi
echo "====================================="

echo ""
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "下一步: 运行配置脚本创建数据库和配置文件"
    echo "  cd $(dirname "$0")"
    echo "  bash deploy/config.sh"
else
    echo "请根据上方 [失败] 提示手动安装对应软件，或联系技术支持"
fi
