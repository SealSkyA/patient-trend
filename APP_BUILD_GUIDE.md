# 患者检查报告趋势 - APP 打包指南

## 一、概述

本文档指导如何将患者检查报告趋势系统打包成 Android/iOS 手机 APP。

| 项目 | 信息 |
|------|------|
| APP 名称 | 患者检查报告趋势 |
| App ID | com.patient.trend |
| 技术栈 | Capacitor + Vue 3 |
| 后端 API | http://www.021897.xyz:35001 |
| Android 最低版本 | Android 7.0 (API 24) |
| iOS 最低版本 | iOS 14.0 |

---

## 二、快速打包（推荐）

### 2.1 一键构建脚本

```bash
cd /workspace/frontend
./build-app.sh
```

该脚本会自动：
1. 安装 Capacitor 依赖
2. 构建前端代码
3. 添加 Android/iOS 平台
4. 同步配置到平台

### 2.2 仅 Android 快速构建

```bash
cd /workspace/frontend
./build-android-fast.sh
```

---

## 三、Android 打包详细说明

### 3.1 环境要求

| 软件 | 版本要求 | 下载地址 |
|------|---------|---------|
| JDK | 11+ | https://adoptium.net |
| Android Studio | 最新版 | https://developer.android.com |
| Android SDK | API 33+ | Android Studio 内安装 |
| Node.js | 18+ | https://nodejs.org |

### 3.2 配置 Android SDK

```bash
# 设置环境变量（~/.bashrc 或 ~/.zshrc）
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

### 3.3 构建 APK

**方式一：使用 Android Studio（推荐）**

```bash
cd /workspace/frontend
npm run build
npx cap sync android
npx cap open android
```

在 Android Studio 中：
1. 等待 Gradle 同步完成（首次同步可能需要下载依赖）
2. 点击菜单 `Build → Build Bundle(s)/APK(s) → Build APK(s)`
3. 等待构建完成
4. APK 位置：`android/app/build/outputs/apk/debug/app-debug.apk`

**方式二：命令行构建**

```bash
cd /workspace/frontend/android
./gradlew assembleRelease
```

APK 位置：`android/app/build/outputs/apk/release/app-release.apk`

### 3.4 签名 APK（发布用）

1. **生成签名密钥**

```bash
keytool -genkey -v -keystore patient-trend.keystore -alias patient-trend \
  -keyalg RSA -keysize 2048 -validity 10000
```

2. **配置签名**

编辑 `android/app/build.gradle`:

```gradle
android {
    ...
    signingConfigs {
        release {
            storeFile file('patient-trend.keystore')
            storePassword '你的密钥库密码'
            keyAlias 'patient-trend'
            keyPassword '你的密钥密码'
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

3. **构建签名 APK**

```bash
./gradlew assembleRelease
```

---

## 四、iOS 打包详细说明

### 4.1 环境要求

| 软件/服务 | 要求 |
|----------|------|
| macOS | 必须要有 macOS |
| Xcode | 最新版 |
| Apple Developer 账号 | 付费账号（$99/年） |
| CocoaPods | `sudo gem install cocoapods` |

### 4.2 构建 IPA

```bash
cd /workspace/frontend
npm run build
npx cap sync ios
npx cap open ios
```

在 Xcode 中：
1. 选择 Team（需要 Apple Developer 账号）
2. 设置 Bundle Identifier（如 com.patient.trend）
3. 选择 `Product → Archive`
4. 等待归档完成
5. 在 Organizer 中 Export IPA

### 4.3 测试版分发

**TestFlight 分发：**
1. 在 App Store Connect 创建 App
2. 上传 IPA 到 TestFlight
3. 添加测试员
4. 测试员通过 TestFlight App 安装

---

## 五、后端 API 配置

### 5.1 前端 API 地址

已配置在 `.env.production`:

```env
VITE_API_BASE_URL=http://www.021897.xyz:35001
```

### 5.2 后端部署

确保后端在服务器上运行：

```bash
# 服务器上执行
cd /workspace/backend
nohup python3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 35001 > backend.log 2>&1 &

# 查看日志
tail -f backend.log

# 测试 API
curl http://www.021897.xyz:35001/api/health
```

### 5.3 防火墙配置

确保服务器开放 35001 端口：

```bash
# 如果使用 firewalld
sudo firewall-cmd --permanent --add-port=35001/tcp
sudo firewall-cmd --reload

# 如果使用 ufw
sudo ufw allow 35001/tcp
```

### 5.4 HTTPS 建议（生产环境）

生产环境建议使用 HTTPS：

```bash
# 使用 Nginx 反向代理 + Let's Encrypt
sudo apt-get install -y nginx certbot python3-certbot-nginx

sudo certbot --nginx -d www.021897.xyz
```

Nginx 配置示例：

```nginx
server {
    listen 443 ssl;
    server_name www.021897.xyz;

    ssl_certificate /etc/letsencrypt/live/www.021897.xyz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.021897.xyz/privkey.pem;

    location /api/ {
        proxy_pass http://127.0.0.1:35001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 六、常见问题排查

### 6.1 Android 构建失败

**问题：Gradle 同步失败**

```bash
# 清理缓存
cd android
./gradlew clean
./gradlew --stop

# 删除 .gradle 目录重试
rm -rf .gradle
./gradlew sync
```

**问题：找不到 Android SDK**

```bash
# 检查 SDK 路径
echo $ANDROID_HOME

# 在 android/local.properties 中指定
sdk.dir=/home/user/Android/Sdk
```

### 6.2 iOS 构建失败

**问题：CocoaPods 安装失败**

```bash
# 安装 CocoaPods
sudo gem install cocoapods

# 或使用 Homebrew
brew install cocoapods

# 同步 pods
cd ios
pod install
```

**问题：签名错误**

1. 检查 Apple Developer 账号是否有效
2. 检查 Bundle Identifier 是否唯一
3. 在 Xcode 中重新选择 Team

### 6.3 APP 无法连接后端

**检查清单：**
1. [ ] 后端服务是否运行
2. [ ] 服务器防火墙是否开放端口
3. [ ] APP 内 API 地址是否正确
4. [ ] Android 是否允许 Cleartext（HTTP）

**Android Cleartext 配置：**

编辑 `android/app/src/main/AndroidManifest.xml`:

```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

---

## 七、APP 更新流程

### 7.1 版本更新

1. 修改版本号：`android/app/build.gradle`

```gradle
android {
    defaultConfig {
        versionCode 2
        versionName "1.1.0"
    }
}
```

2. 重新构建前端
3. 同步到平台
4. 重新打包

### 7.2 热更新（仅内容更新）

```bash
# 使用 Capacitor Live Updates（需要付费）
# 或手动推送更新

# 构建新版本
npm run build
npx cap sync

# 通知用户下载新版本
```

---

## 八、文件结构

```
/workspace/frontend/
├── android/                  # Android 项目
│   ├── app/
│   │   ├── build.gradle      # Android 配置
│   │   └── src/main/
│   │       └── AndroidManifest.xml
│   └── gradle.properties
├── ios/                      # iOS 项目
│   ├── App/
│   │   └── App.xcworkspace
│   └── Podfile
├── dist/                     # 构建输出
├── capacitor.config.ts       # Capacitor 配置
├── build-app.sh              # 打包脚本
├── build-android-fast.sh     # 快速构建脚本
└── .env.production           # 生产环境配置
```

---

## 九、常用命令速查

| 操作 | 命令 |
|------|------|
| 安装 Capacitor | `npm install @capacitor/core @capacitor/cli --save-dev` |
| 构建前端 | `npm run build` |
| 同步平台 | `npx cap sync` |
| 打开 Android Studio | `npx cap open android` |
| 打开 Xcode | `npx cap open ios` |
| 检查设备 | `npx cap run android --list` |
| 运行到设备 | `npx cap run android` |

---

## 十、联系与支持

如遇问题，请检查：
1. 构建日志输出
2. 后端服务状态
3. 网络连接和防火墙
4. Capacitor 版本兼容性

建议保存此文档，便于后续维护参考。
