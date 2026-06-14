#!/bin/bash

# 患者检查报告趋势 - APP 打包脚本
# 适用于 Android/iOS

set -e

echo "======================================"
echo "患者检查报告趋势 - APP 打包脚本"
echo "======================================"
echo ""

cd /workspace/frontend

# 1. 安装依赖
echo "📦 安装 Capacitor 依赖..."
npm install @capacitor/core @capacitor/cli --save-dev
npm install @capacitor/android @capacitor/ios --save-dev
npm install @capacitor/splash-screen @capacitor/keyboard --save-dev

# 2. 构建前端
echo "🔨 构建前端..."
npm run build

# 3. 初始化 Capacitor（如果未初始化）
if [ ! -f "capacitor.config.ts" ]; then
  echo "📱 初始化 Capacitor..."
  npx cap init "患者检查报告趋势" "com.patient.trend" --web-dir=dist
fi

# 4. 添加平台
echo "📲 添加平台..."

# Android
if [ ! -d "android" ]; then
  echo "  → 添加 Android 平台..."
  npx cap add android
else
  echo "  → Android 平台已存在"
fi

# iOS (仅 macOS)
if [ "$(uname)" = "Darwin" ]; then
  if [ ! -d "ios" ]; then
    echo "  → 添加 iOS 平台..."
    npx cap add ios
  else
    echo "  → iOS 平台已存在"
  fi
fi

# 5. 同步到平台
echo "🔄 同步到平台..."
npx cap sync

echo ""
echo "======================================"
echo "✅ 打包准备完成！"
echo "======================================"
echo ""
echo "下一步操作："
echo ""
echo "【Android 打包】"
echo "1. 打开 Android Studio:"
echo "   npx cap open android"
echo ""
echo "2. 等待 Gradle 同步完成"
echo ""
echo "3. 构建 APK:"
echo "   Build → Build Bundle(s)/APK(s) → Build APK(s)"
echo ""
echo "4. APK 输出位置:"
echo "   android/app/build/outputs/apk/debug/app-debug-release.apk"
echo ""
echo "【iOS 打包】(需要 macOS)"
echo "1. 打开 Xcode:"
echo "   npx cap open ios"
echo ""
echo "2. 配置签名:"
echo "   选择 Team 和 Bundle Identifier"
echo ""
echo "3. 构建:"
echo "   Product → Archive → Export IPA"
echo ""
echo "======================================"
