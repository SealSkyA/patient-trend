# ============================================
# 「报告管理」APP — Windows 端打包脚本
# 在 Windows 电脑上运行，自动完成构建和生成 APK
# ============================================

$ErrorActionPreference = "Continue"

function Log-Ok   { param($msg) Write-Host "[成功] $msg" -ForegroundColor Green }
function Log-Err  { param($msg) Write-Host "[错误] $msg" -ForegroundColor Red }
function Log-Info { param($msg) Write-Host "[信息] $msg" -ForegroundColor Yellow }
function Log-Step { param($msg) Write-Host "`n--- $msg ---`n" -ForegroundColor Cyan }

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"

Log-Step "检查环境"

# 检查 Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Log-Err "Node.js 未安装"
    Log-Info "请访问 https://nodejs.org 下载并安装 LTS 版本"
    exit 1
}
Log-Ok "Node.js: $(node -v)"

# 检查 Java
try {
    $javaVer = java -version 2>&1 | Select-String '"(17|21)' | Select-Object -First 1
    if (!$javaVer) {
        $javaRaw = java -version 2>&1 | Select-Object -First 1
        Log-Ok "Java: $javaRaw (建议 JDK 17 或 21)"
    } else {
        Log-Ok "Java: $javaVer"
    }
} catch {
    Log-Err "Java 未安装"
    Log-Info "请访问 https://adoptium.net 下载 JDK 17"
    exit 1
}

# 检查 ANDROID_HOME
$androidHome = $env:ANDROID_HOME
if (!$androidHome -or !(Test-Path $androidHome)) {
    Log-Err "ANDROID_HOME 未设置或路径无效"
    Log-Info "请打开 Android Studio → SDK Manager，找到 SDK 安装路径"
    Log-Info "然后设置环境变量: ANDROID_HOME = SDK 路径"
    exit 1
}
Log-Ok "Android SDK: $androidHome"

# -------------------------------------------
# 1. 检查前端配置
# -------------------------------------------
Log-Step "检查前端配置"

$prodEnv = Join-Path $FrontendDir ".env.production"
if (Test-Path $prodEnv) {
    $content = Get-Content $prodEnv
    $backendUrl = ($content | Where-Object { $_ -match "VITE_API_BASE_URL=" }) -replace "VITE_API_BASE_URL=", ""
    Log-Ok "后端 API 地址: $backendUrl"
} else {
    Log-Err "找不到 $prodEnv"
    Log-Info "请用记事本打开此文件，写入: VITE_API_BASE_URL=http://你的后端地址:35001"
    exit 1
}

# -------------------------------------------
# 2. 安装依赖
# -------------------------------------------
Log-Step "安装前端依赖"

Set-Location $FrontendDir

if (Test-Path "node_modules") {
    Log-Info "更新现有依赖..."
    npm install 2>&1 | Select-Object -Last 1 | Out-Null
} else {
    Log-Info "首次安装依赖，可能需要 1-3 分钟..."
    npm install 2>&1 | Select-Object -Last 1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Log-Info "失败，切换到淘宝镜像..."
        npm config set registry https://registry.npmmirror.com
        npm install 2>&1 | Select-Object -Last 1 | Out-Null
    }
}
Log-Ok "依赖安装完成"

# -------------------------------------------
# 3. 构建前端
# -------------------------------------------
Log-Step "构建前端"

npm run build 2>&1 | Select-Object -Last 3 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Log-Err "前端构建失败"
    exit 1
}

if (Test-Path "dist\index.html") {
    Log-Ok "前端构建完成: frontend\dist\"
} else {
    Log-Err "构建产物不存在"
    exit 1
}

# -------------------------------------------
# 4. 同步到 Android
# -------------------------------------------
Log-Step "同步到 Android"

if (Test-Path "android") {
    Log-Info "更新现有 Android 项目..."
    npx cap sync android 2>&1 | Select-Object -Last 3 | Out-Null
} else {
    Log-Info "创建新 Android 项目..."
    npx cap add android 2>&1 | Select-Object -Last 3 | Out-Null
}

# -------------------------------------------
# 5. 打开 Android Studio
# -------------------------------------------
Log-Step "打开 Android Studio"

Log-Info "即将打开 Android Studio..."
Log-Info "打开后请等待项目同步完成（查看底部进度条）"
Log-Info "然后: Build → Build Bundle(s) / APK(s) → Build APK(s)"
Log-Info "构建完成后会弹出 APK 所在文件夹"
Log-Info ""
Log-Info "APK 默认位置: frontend\android\app\build\outputs\apk\debug\app-debug.apk"
Log-Info ""
Log-Info "按 Enter 键打开 Android Studio..."
Read-Host

npx cap open android
