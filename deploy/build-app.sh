#!/bin/bash
# ============================================
# 「报告管理」APP — 前端构建 + Android APK 打包（Linux）
# 适用于在 Linux 服务器上直接构建 Android APK
# 需要先安装 JDK、SDK 和 capacitor
# ============================================

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_ok()   { echo -e "${GREEN}[成功]${NC} $1"; }
log_err()  { echo -e "${RED}[错误]${NC} $1"; }
log_info() { echo -e "${YELLOW}[信息]${NC} $1"; }
log_step() { echo -e "\n${BLUE}--- $1 ---${NC}\n"; }

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

log_step "检查环境"

# 检查 Node.js
if ! command -v node &>/dev/null; then
    log_err "Node.js 未安装"
    exit 1
fi
log_ok "Node.js: $(node -v)"

# 检查 JDK
if ! command -v java &>/dev/null; then
    log_err "JDK 未安装，运行: sudo dnf install -y java-17-openjdk"
    exit 1
fi
log_ok "JDK: $(java -version 2>&1 | head -1)"

# 检查 Android SDK
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    log_err "ANDROID_HOME 未设置"
    log_info "请先安装 Android SDK 并设置: export ANDROID_HOME=/path/to/android-sdk"
    exit 1
fi
log_ok "Android SDK: ${ANDROID_HOME:-$ANDROID_SDK_ROOT}"

# -------------------------------------------
# 1. 检查前端配置
# -------------------------------------------
log_step "检查前端配置"

PROD_ENV="${FRONTEND_DIR}/.env.production"
if [ -f "$PROD_ENV" ]; then
    BACKEND_URL=$(grep "VITE_API_BASE_URL=" "$PROD_ENV" | cut -d'=' -f2-)
    log_ok "后端 API 地址: ${BACKEND_URL}"
else
    log_err "找不到 ${PROD_ENV}"
    log_info "请先运行: bash deploy/config.sh"
    exit 1
fi

# 检查 APP 配置
CAP_FILE="${FRONTEND_DIR}/capacitor.config.ts"
if [ ! -f "$CAP_FILE" ]; then
    log_err "找不到 $CAP_FILE"
    exit 1
fi
log_ok "APP 配置已就绪"

# -------------------------------------------
# 2. 安装依赖
# -------------------------------------------
log_step "安装依赖"

cd "$FRONTEND_DIR"

if [ -d "node_modules" ]; then
    log_info "检测到 node_modules，尝试更新..."
    npm install 2>&1 | tail -1 || {
        log_info "npm install 失败，切换到淘宝镜像..."
        npm config set registry https://registry.npmmirror.com
        npm install 2>&1 | tail -1
    }
else
    log_info "首次安装依赖..."
    npm install 2>&1 | tail -1 || {
        log_info "失败，切换到淘宝镜像..."
        npm config set registry https://registry.npmmirror.com
        npm install 2>&1 | tail -1
    }
fi
log_ok "依赖安装完成"

# -------------------------------------------
# 3. 构建前端
# -------------------------------------------
log_step "构建前端"

npm run build 2>&1 | tail -3 || {
    log_err "前端构建失败"
    exit 1
}

if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    log_ok "前端构建完成: ${FRONTEND_DIR}/dist/"
else
    log_err "构建产物不存在"
    exit 1
fi

# -------------------------------------------
# 4. 添加/更新 Android 平台
# -------------------------------------------
log_step "同步到 Android"

if [ -d "android" ]; then
    log_info "更新现有 Android 项目..."
    npx cap sync android 2>&1 | tail -3
else
    log_info "创建新 Android 项目..."
    npx cap add android 2>&1 | tail -3
fi

# -------------------------------------------
# 5. 构建 APK（调试版）
# -------------------------------------------
log_step "构建 APK"

if [ -d "android" ]; then
    cd android
    if [ -f "gradlew" ]; then
        # Linux 权限处理
        chmod +x gradlew 2>/dev/null || true
        # 构建调试版 APK
        ./gradlew assembleDebug 2>&1 | tail -5
        
        # 查找 APK
        APK=$(find . -name "app-debug.apk" -type f | head -1)
        if [ -n "$APK" ]; then
            log_ok "APK 构建完成"
            log_ok "APK 位置: ${FRONTEND_DIR}/android/${APK#./}"
        else
            log_err "找不到 app-debug.apk"
        fi
    else
        log_err "gradlew 文件不存在"
    fi
else
    log_err "android 目录不存在"
    exit 1
fi

# -------------------------------------------
# 6. 汇总
# -------------------------------------------
echo ""
echo "====================================="
echo "  构建完成!"
echo "====================================="
echo ""
echo "APK 文件: ${FRONTEND_DIR}/android/app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "安装到手机 (需连接 USB 调试):"
echo "  adb install ${FRONTEND_DIR}/android/app/build/outputs/apk/debug/app-debug.apk"
echo ""
