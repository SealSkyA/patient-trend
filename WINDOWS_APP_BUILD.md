# Windows 打包 APP 指南（不影响服务器）

## 一、概述

本指南指导如何在 **Windows 电脑** 上打包 Android APP，**不会影响服务器已部署的环境**。

### 安全说明

| 项目 | 说明 |
|------|------|
| **服务器** | 保持运行，不需要任何操作 |
| **后端 API** | 保持 `www.021897.xyz:35001` 运行即可 |
| **数据库** | 不需要动，数据都在服务器 |
| **前端打包** | 在 Windows 本地完成，不影响服务器 |

---

## 二、Windows 安装必要工具

### 2.1 安装 Node.js

1. 访问 https://nodejs.org
2. 下载 **LTS 版本**（20.x）
3. 运行安装程序，一直点击下一步
4. 安装完成后，打开 PowerShell 验证：

```powershell
node -v
npm -v
```

### 2.2 安装 Android Studio

1. 访问 https://developer.android.com
2. 下载 **Android Studio**
3. 运行安装程序
4. 安装完成后，打开 Android Studio：
   - **同意许可协议**
   - 点击 `Finish`
   - 等待下载 Android SDK 和 Gradle（较耗时）
   - 进入欢迎界面即可

### 2.3 安装 Git（可选，如果已有代码可跳过）

1. 访问 https://git-scm.com
2. 下载安装程序
3. 运行安装程序

---

## 三、准备项目代码

### 3.1 新建目录（不影响服务器）

```powershell
# 创建新目录
mkdir C:\Apps\patient-trend-app
cd C:\Apps\patient-trend-app
```

### 3.2 获取项目代码

**方式一：从 Git 仓库克隆（推荐）**

```powershell
# 克隆项目
git clone <你的 Git 仓库地址> .

# 或从服务器下载打包好的代码
# 在服务器上执行：
# zip -r /tmp/patient-trend.zip /workspace --exclude *.git*
# 然后下载到 C:\Apps\patient-trend-app 解压
```

**方式二：手动复制代码**

1. 从服务器下载 `/workspace` 目录（排除 `.git`）
2. 解压到 `C:\Apps\patient-trend-app`

---

## 四、Windows 打包步骤

### 4.1 安装依赖

```powershell
cd C:\Apps\patient-trend-app\frontend

# 安装前端依赖
npm install

# 安装 Capacitor
npm install @capacitor/core @capacitor/cli --save-dev
npm install @capacitor/android --save-dev
npm install @capacitor/splash-screen @capacitor/keyboard --save-dev
```

### 4.2 检查配置

**确保以下文件存在：**

- `capacitor.config.ts` - Capacitor 配置
- `.env.production` - API 地址配置（www.021897.xyz:35001）

### 4.3 构建前端

```powershell
# 构建前端代码
npm run build
```

成功后会生成 `dist/` 目录。

### 4.4 添加 Android 平台

```powershell
# 初始化 Capacitor（如果之前没初始化）
npx cap init "患者检查报告趋势" "com.patient.trend" --web-dir=dist

# 添加 Android 平台
npx cap add android
```

### 4.5 同步到 Android

```powershell
# 同步前端代码和配置到 Android
npx cap sync
```

### 4.6 打开 Android Studio

```powershell
# 打开 Android Studio
npx cap open android
```

---

## 五、Android Studio 构建 APK

### 5.1 等待 Gradle 同步

第一次打开 Android Studio 会：
- 下载 Gradle（约 100MB）
- 下载 Android SDK 组件
- 同步项目依赖

**耗时 5-15 分钟**，请耐心等待右下角进度条完成。

### 5.2 构建 APK

1. 点击菜单 `Build → Build Bundle(s)/APK(s) → Build APK(s)`
2. 等待构建完成（约 2-5 分钟）
3. 弹出提示 "APK(s) generated successfully"

### 5.3 获取 APK 文件

APK 路径：
```
C:\Apps\patient-trend-app\frontend\android\app\build\outputs\apk\debug\app-debug.apk
```

---

## 六、安装到手机测试

### 6.1 通过 USB 安装

1. 手机开启 **开发者选项** 和 **USB 调试**
2. 用 USB 线连接电脑
3. 在 Android Studio 中点击 `Run`（绿色三角）
4. 选择你的设备，点击 OK

### 6.2 手动安装

1. 将 `app-debug.apk` 复制到手机
2. 在手机上打开 APK 文件
3. 允许安装未知来源应用
4. 完成安装

---

## 七、常见问题

### 7.1 Gradle 同步失败

**错误：Could not resolve all artifacts**

```powershell
cd C:\Apps\patient-trend-app\frontend\android
.\gradlew clean
.\gradlew --stop
# 重新打开 Android Studio
```

**错误：SDK 组件缺失**

打开 Android Studio：
1. `Tools → SDK Manager`
2. 安装缺失的组件
3. 点击 `Apply`

### 7.2 npx cap add android 失败

**错误：Android SDK not found**

在 Android Studio 中：
1. `Tools → SDK Manager`
2. 记下 SDK 路径（如 `C:\Users\YourName\AppData\Local\Android\Sdk`）
3. 在 `android/local.properties` 中添加：
   ```
   sdk.dir=C:\\Users\\YourName\\AppData\\Local\\Android\\Sdk
   ```

### 7.3 构建 APK 失败

**错误：Java home 问题**

1. 打开 Android Studio
2. `File → Settings → Build, Execution, Deployment → Build Tools → Gradle`
3. 设置 `Gradle JDK` 为 Android Studio 自带的版本
4. 点击 `Apply`

### 7.4 APP 无法连接后端

**检查后端是否运行：**

```powershell
# 测试 API 是否可访问
curl http://www.021897.xyz:35001/api/health
```

**Android Cleartext 配置：**

编辑 `android/app/src/main/AndroidManifest.xml`，添加：

```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

---

## 八、常用命令速查（PowerShell）

| 操作 | 命令 |
|------|------|
| 安装依赖 | `cd frontend && npm install` |
| 构建前端 | `npm run build` |
| 同步平台 | `npx cap sync` |
| 打开 Android Studio | `npx cap open android` |
| 清理 Gradle | `cd android && .\gradlew clean` |

---

## 九、服务器保持状态

### 无需操作的服务

| 服务 | 状态 | 说明 |
|------|------|------|
| MySQL | ✅ 继续运行 | 用户数据 |
| 后端 API | ✅ 继续运行 | `www.021897.xyz:35001` |
| 前端服务 | ✅ 继续运行 | `www.021897.xyz:35000`（如有） |
| Nginx | ✅ 继续运行 | 反向代理（如有） |

### APP 使用的 API

```
http://www.021897.xyz:35001/api/
├── POST /api/auth/login      # 登录
├── GET  /api/patients/       # 患者列表
├── GET  /api/dashboard/:id   # 仪表板
├── GET  /api/reports/        # 报告列表
├── POST /api/reports/        # 创建报告
└── ...
```

---

## 十、注意事项

### 安全提示

1. **不要在 Windows 上修改后端代码** - 仅需前端代码即可打包
2. **不要修改服务器配置** - 服务器保持原有状态
3. **备份 APK** - 构建成功后，复制 APK 到安全位置

### 性能建议

1. **预留磁盘空间** - Android Studio + SDK 约需 10GB
2. **内存充足** - 建议 8GB 以上内存
3. **首次构建较慢** - 下载依赖需时，后续会快很多

### 发布建议

1. **测试版 APK** - 先用 debug 版本测试
2. **正式版签名** - 发布前需要签名（见打包指南）
3. **更新机制** - APP 内提示用户下载新版本

---

## 十一、联系与支持

如遇到问题：
1. 查看 Android Studio 构建日志
2. 检查后端 API 是否可访问
3. 确认 Capacitor 版本兼容性

建议保存此文档，便于后续打包参考。

---

## 附录：环境检查清单

打包前确认：

- [ ] Node.js 已安装（`node -v`）
- [ ] npm 可用（`npm -v`）
- [ ] Android Studio 已安装
- [ ] Android SDK 已安装
- [ ] 项目代码在 `C:\Apps\patient-trend-app`
- [ ] 后端 API 可访问（`www.021897.xyz:35001`）
- [ ] 前端已构建成功（`dist/` 目录存在）
- [ ] Android 平台已添加（`android/` 目录存在）
- [ ] Gradle 同步成功（Android Studio 无错误）

**全部勾选后，点击 Build 即可生成 APK！**
