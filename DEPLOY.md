# 「报告管理」APP — 部署手册（新手从零开始）

> 本手册面向**零技术基础**的用户，每一步都给出具体文件路径、具体改什么、改完怎么验证。

---

## 零、你需要什么

| 东西 | 干什么用的 | 在哪 |
|------|-----------|------|
| 一台 Linux 服务器（openEuler / Ubuntu / CentOS） | 运行后端和数据库 | 云端或本地 |
| Windows 电脑 | 打包 Android APK | 本地 |
| GitHub 账号 | 下载代码 | https://github.com |

---

## 一、项目文件结构速查

```
项目根目录
│
├── .env  ← 【后端】数据库密码在这里改（git 忽略）
│
├── deploy/                    ← 【部署脚本目录】
│   ├── setup.sh               ← 自动安装环境（Python/Node.js/MySQL/Git）
│   ├── config.sh              ← 交互式配置（引导输入数据库信息、地址）
│   ├── build-app.sh           ← Linux 上构建 APK
│   └── build-app-windows.ps1  ← Windows 上构建 APK
│
├── start.sh                   ← 一键启动服务（自动检查配置、安装依赖、启动前后端）
│
├── backend/                   # 后端（FastAPI Python）
│   ├── config.py              #  后端配置读取逻辑（一般不用改）
│   ├── database.py            #  数据库连接池配置
│   ├── main.py                #  后端启动入口
│   ├── migrations/            #  数据库迁移（自动创建索引）
│   └── routers/               #  各 API 接口
│
├── frontend/                  # 前端（Vue 3 + TypeScript）
│   ├── .env.development       ← 【前端开发】开发服务器 API 地址（已忽略）
│   ├── .env.production        ← 【前端打包/APP】后端 API 地址（已忽略）
│   ├── capacitor.config.ts    #  APP 名称、Android 配置
│   ├── vite.config.ts         #  前端开发服务器配置
│   └── src/
│       ├── api/client.ts      #  前端 API 客户端（读取 .env）
│       └── views/
│           └── DashboardMobile.vue  #  APP 首页
```

---

## 二、Linux 服务器部署（推荐：脚本一键完成）

### 2.1 下载代码

```bash
cd /opt
git clone https://github.com/SealSkyA/patient-trend.git
cd patient-trend
```

### 2.2 一键安装环境 + 配置 + 启动

```bash
# 给脚本执行权限
chmod +x deploy/*.sh start.sh

# 步骤 1: 安装 Python 3.11、Node.js、MySQL、Git（方案A 失败自动切换方案B/C/D）
bash deploy/setup.sh

# 步骤 2: 交互式配置数据库、密钥、后端地址（按提示输入密码等信息）
bash deploy/config.sh

# 步骤 3: 一键启动前后端
bash start.sh
```

**就这么简单！** 每个脚本都有：
- 自动检测已有软件（不会重复安装）
- 多种备选安装方案（dnf → apt → 源码编译）
- 错误时清晰提示，告诉用户怎么处理
- 配置时主动询问用户（数据库密码、密钥、服务器地址）

### 2.3 手动部署（如脚本失败时参考）

如果脚本无法正常运行，可按以下步骤手动操作：

#### 安装环境

```bash
# Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
# 备选: sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Node.js
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs
# 备选: 使用 nvm 或从 nodejs.org 下载预编译版本

# MySQL
sudo dnf install -y mysql-server
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Git
sudo dnf install -y git
```

#### 创建数据库

```bash
mysql -u root -p
```

在 MySQL 命令行中执行：

```sql
CREATE DATABASE IF NOT EXISTS patient_trend
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'patient_user'@'localhost' 
  IDENTIFIED BY '你的密码';

GRANT ALL PRIVILEGES ON patient_trend.* TO 'patient_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

验证：
```bash
mysql -u patient_user -p'你的密码' patient_trend -e "SELECT '连接成功' AS status;"
```

#### 安装后端依赖

```bash
cd /opt/patient-trend/backend
python3.11 -m pip install -r requirements.txt --break-system-packages
```

#### 创建后端配置文件

```bash
# 在项目根目录创建 .env 文件
cd /opt/patient-trend

# 生成密钥
SECRET_KEY=$(openssl rand -hex 32)

# 创建 .env（把下面内容中的数据库密码换成你实际的密码）
cat > .env << EOF
DATABASE_URL=mysql+aiomysql://patient_user:你的密码@localhost:3306/patient_trend?charset=utf8mb4
DATABASE_ECHO=false
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
DEBUG=false
EOF
```

#### 创建前端配置文件

```bash
# 开发环境（本地调试）
cat > frontend/.env.development << EOF
VITE_API_BASE_URL=/api
VITE_SERVER_URL=http://localhost:35001
EOF

# 生产环境（APP 打包 / 公网访问）
# 把地址改成你的服务器 IP 或域名
cat > frontend/.env.production << EOF
VITE_API_BASE_URL=http://你的服务器IP:35001
EOF
```

#### 安装前端依赖

```bash
cd /opt/patient-trend/frontend
npm install
```

#### 启动服务

```bash
cd /opt/patient-trend
bash start.sh
```

---

## 三、前端部署（Linux 服务器）

### 3.1 启动开发服务器（本地调试）

```bash
cd /opt/patient-trend
bash start.sh
```

### 3.2 构建前端（用于打包 APP）

```bash
cd /opt/patient-trend/frontend

# 确保 .env.production 中后端地址正确

npm run build
```

构建完成后，`frontend/dist/` 目录包含静态文件。

---

## 四、Android APP 打包（Windows 电脑）

> 本节在** Windows 电脑**上操作，不是 Linux 服务器。

### 4.1 安装必备软件

| 软件 | 下载地址 | 说明 |
|------|----------|------|
| Node.js v18+ | https://nodejs.org | 选 LTS 版，安装时全部默认 |
| Git | https://git-scm.com | 默认设置安装即可 |
| Java JDK 17 | https://adoptium.net | 安装后验证：`java -version` |
| Android Studio | https://developer.android.com/studio | 安装后打开 Android Studio → Tools → SDK Manager → 勾选 Android SDK 平台（API 34 或 35）并下载 |

### 4.2 下载项目并安装依赖

打开**命令提示符**（Win + R → 输入 `cmd` → 回车）：

```powershell
# 选择一个目录来放项目
cd C:\Users\你的用户名\Desktop

# 下载代码
git clone https://github.com/SealSkyA/patient-trend.git
cd patient-trend\frontend
```

安装依赖：

```powershell
npm install
```

### 4.3 用脚本一键打包

PowerShell 中执行：

```powershell
cd C:\Users\你的用户名\Desktop\patient-trend\deploy
.\build-app-windows.ps1
```

脚本会自动：
1. 检查 Node.js、Java、Android SDK（缺失时报错并给出下载地址）
2. 安装前端依赖（失败自动切换淘宝镜像）
3. 构建前端
4. 同步到 Android
5. 打开 Android Studio → 提示你 Build → Build APK(s)

APK 位置：
```
frontend\android\app\build\outputs\apk\debug\app-debug.apk
```

### 4.4 下载项目并手动打包

如果脚本无法运行，按以下步骤手动操作：

打开**命令提示符**（Win + R → 输入 `cmd` → 回车）：

```powershell
# 1. 下载项目
cd C:\Users\你的用户名\Desktop
git clone https://github.com/SealSkyA/patient-trend.git
cd patient-trend\frontend

# 2. 配置后端地址（用记事本打开 .env.production）
#    VITE_API_BASE_URL=http://你的服务器IP:35001

# 3. 安装依赖
npm install
# 如果失败: npm config set registry https://registry.npmmirror.com

# 4. 构建
npm run build

# 5. 添加 Android 平台（首次执行需要，后续不需要）
npx cap add android

# 6. 同步
npx cap sync android

# 7. 打开 Android Studio
npx cap open android
```

### 4.5 安装打包 APK

在 Android Studio 中：

1. 等待项目加载完成（左下角进度条走完，显示 "Synced"）
2. 顶部菜单：**Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
3. 等待底部显示 "BUILD SUCCESSFUL"
4. 弹出的 "Open in Explorer" 直接点击，APK 就在打开的文件夹里

APK 位置通常在：
```
frontend\android\app\build\outputs\apk\debug\app-debug.apk
```

把 APK 传到手机上，直接安装。

### 4.6 正式版 APK（签名、可发应用市场）

1. 顶部菜单：**Build** → **Generate Signed Bundle / APK**
2. 选择 **APK** → Next
3. **如果已有签名密钥**：选择现有 keystore 文件，输入密码
   **如果没有密钥**：点击 "Create new..." 创建新的
   - Key store path：选一个你能找到的位置
   - Password：设一个密码，**一定要记住**
   - Key alias：填 `patient-trend`
   - Validity（年）：填 `25`
   - 填写组织信息 → OK
4. 选择 **release** 构建类型
5. 点击 **Finish**，等待构建完成
6. 同样会弹出 "Open in Explorer"，APK 在：
```
frontend\android\app\build\outputs\apk\release\app-release.apk
```

### 4.7 安装到手机

```bash
# 手机打开 USB 调试，连接电脑后
cd frontend\android
.\gradlew installDebug
```

或直接手机扫码安装、通过微信发送 APK 安装。

### 4.8 每次更新 APP 的完整流程

以后每次代码有更新，按以下步骤重新打包：

```powershell
cd frontend

# 1. 拉取最新代码
git pull

# 2. 确认 .env.production 里的后端地址正确
#    如果不正确，用记事本打开修改

# 3. 安装最新依赖
npm install

# 4. 构建前端
npm run build

# 5. 同步到 Android
npx cap sync android

# 6. 打开 Android Studio 打包
npx cap open android
# 然后 Build → Build APK(s)
```

### 4.9 常见问题

| 问题 | 解决 |
|------|------|
| `npx cap add android` 报错 | 确保已装 Java 17 和 Android SDK |
| APP 显示 "无法连接后端" | 检查 `.env.production` 地址是否正确，手机和服务器网络是否通 |
| Android Studio 一直加载 | File → Invalidate Caches → Invalidate and Restart |
| `gradlew` 权限不够 | Windows 上直接运行 `.\gradlew`，不要用 `./` |
| 构建后 APP 还是旧的内容 | 执行 `npx cap sync android` 再重新 Build APK |

---

## 五、运维操作

### 5.1 一键更新

```bash
cd /opt/patient-trend
bash start.sh
```

脚本会自动：
- 停止旧进程
- 自动安装新依赖（如有）
- 启动前后端

### 5.2 查看日志

```bash
tail -f /opt/patient-trend/logs/backend.log   # 后端
tail -f /opt/patient-trend/logs/frontend.log  # 前端
# 按 Ctrl+C 退出
```

### 5.3 停止服务

直接 Ctrl+C 退出 `start.sh`，或手动停止：

```bash
pkill -f "uvicorn.*backend.main:app"
pkill -f "npm run dev"
```

### 5.4 数据库备份

```bash
mysqldump -u patient_user -p'你的密码' patient_trend > /root/patient_trend_$(date +%Y%m%d).sql
```

---

## 六、配置文件速查表

| 配置文件 | 完整路径 | 改什么 | 改完要不要重启 |
|----------|---------|--------|---------------|
| **后端 .env** | `/opt/patient-trend/.env` | 数据库密码、SECRET_KEY | **是**，重启后端 |
| **前端开发 .env** | `/opt/patient-trend/frontend/.env.development` | 开发用，一般不用改 | 否，开发服务器自动热更新 |
| **前端生产 .env** | `/opt/patient-trend/frontend/.env.production` | **后端 API 地址** | **是**，重新 `npm run build` |
| **APP 配置** | `frontend/capacitor.config.ts` | APP 名称、包名 | **是**，重新 `npx cap sync` + 构建 |

---

## 七、端口说明

| 端口 | 用途 | 对外 |
|------|------|------|
| 35000 | 前端 / Nginx | 浏览器访问 |
| 35001 | 后端 API | APP 和浏览器调用 |
| 3306 | MySQL | 仅限服务器内部 |

防火墙开放 35000 和 35001：

```bash
sudo firewall-cmd --permanent --add-port=35000/tcp
sudo firewall-cmd --permanent --add-port=35001/tcp
sudo firewall-cmd --reload
```

---

## 八、验证清单

部署完成后，逐项检查：

| 序号 | 检查项 | 命令/操作 | 预期结果 |
|------|--------|----------|---------|
| 1 | MySQL 运行中 | `systemctl status mysqld` | `active (running)` |
| 2 | 数据库连接 | `mysql -u patient_user -p'密码' patient_trend -e "SHOW TABLES;"` | 列出所有表 |
| 3 | 后端运行 | `curl http://localhost:35001/api/health` | `{"status":"ok"...}` |
| 4 | 前端运行 | 浏览器打开 `http://服务器IP:35000` | 看到登录页面 |
| 5 | 后端 API 文档 | 浏览器打开 `http://服务器IP:35001/api/docs` | Swagger 界面 |
| 6 | 数据库迁移 | `tail -5 logs/backend.log` | 看到 `Executed 7 new statement(s)` |
| 7 | APP 安装 | APK 安装到手机打开 | 能看到登录页面 |
| 8 | APP 连接 | APP 登录成功 | 能看到首页数据 |

---

## 九、技术栈

| 组件 | 技术选型 |
|------|---------|
| 前端 | Vue 3 + TypeScript + Element Plus + ECharts |
| 后台 | FastAPI + SQLAlchemy (async) + Pydantic |
| 数据库 | MySQL 8.0+ |
| 构建工具 | Vite + Capaciotor (Android) |
