# Windows APP 快速打包脚本（PowerShell）
# 自动修复 Cleartext 问题

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "患者检查报告趋势 - APP 打包脚本" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

cd $PSScriptRoot

# 1. 检查依赖
Write-Host "📦 检查依赖..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "  安装依赖..." -ForegroundColor Yellow
    npm install
}

# 2. 构建前端
Write-Host ""
Write-Host "🔨 构建前端..." -ForegroundColor Yellow
npm run build

# 3. 同步到 Android
Write-Host ""
Write-Host "📲 同步到 Android..." -ForegroundColor Yellow
npx cap sync android

# 4. 自动修复 Cleartext 配置
Write-Host ""
Write-Host "🔧 修复 Android HTTP 配置..." -ForegroundColor Yellow
.\fix-android-cleartext.ps1

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✅ 打包准备完成！" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 在 Android Studio 中重新构建项目：" -ForegroundColor White
Write-Host "   npx cap open android" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. 等待 Gradle 同步完成后点击：" -ForegroundColor White
Write-Host "   Build → Rebuild Project" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. 构建 APK：" -ForegroundColor White
Write-Host "   Build → Build Bundle(s)/APK(s) → Build APK(s)" -ForegroundColor Cyan
Write-Host ""
Write-Host "APK 输出位置：" -ForegroundColor Yellow
Write-Host "android\app\build\outputs\apk\debug\app-debug.apk" -ForegroundColor Cyan
Write-Host ""
