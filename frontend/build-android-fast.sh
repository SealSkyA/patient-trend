#!/bin/bash

# 快速构建 Android APK（不打开 Android Studio）
# 需要先安装 Android SDK 和命令行工具

set -e

echo "======================================"
echo "快速构建 Android APK"
echo "======================================"
echo ""

cd /workspace/frontend

# 构建前端
echo "🔨 构建前端..."
npm run build

# 同步到 Android
echo "📲 同步到 Android..."
npx cap sync android

# 使用 Gradle 直接构建 APK
echo "🏗️  使用 Gradle 构建 APK..."
cd android
./gradlew assembleRelease

echo ""
echo "======================================"
echo "✅ APK 构建完成！"
echo "======================================"
echo ""
echo "APK 位置："
echo "android/app/build/outputs/apk/release/app-release.apk"
echo ""
