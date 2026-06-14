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
├── .env  ← 【后端】数据库密码在这里改
│
├── backend/                    # 后端（FastAPI Python）
│   ├── config.py               #  后端配置读取逻辑（一般不用改）
│   ├── database.py             #  数据库连接池配置
│   ├── main.py                 #  后端启动入口
│   ├── migrations/             #  数据库迁移（自动创建索引）
│   └── routers/                #  各 API 接口
│
├── frontend/                   # 前端（Vue 3 + TypeScript）
│   ├── .env.development        ← 【前端开发】开发服务器 API 地址（已忽略，不传 git）
│   ├── .env.production         ← 【前端打包/APP】后端 API 地址（已忽略，不传 git）
│   ├── capacitor.config.ts     #  APP 名称、Android 配置
│   ├── vite.config.ts          #  前端开发服务器配置
│   └── src/
│       ├── api/client.ts       #  前端 API 客户端（读取 .env）
│       └── views/
│           └── DashboardMobile.vue  #  APP 首页
│
└── start.sh                    #  一键启动脚本（开发用）
```

---

## 二、后端部署（Linux 服务器）

### 2.1 安装基础软件

```bash
# 更新系统
sudo dnf update -y

# 安装 Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# 安装 Node.js 20（前端开发用）
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# 安装 Git
sudo dnf install -y git

# 安装 MySQL
sudo dnf install -y mysql-server
sudo systemctl start mysqld
sudo systemctl enable mysqld
```

### 2.2 下载项目

```bash
cd /opt
git clone https://github.com/SealSkyA/patient-trend.git
cd patient-trend
```

### 2.3 创建数据库

```bash
# 登录 MySQL
mysql -u root -p
```

进入 MySQL 后，逐行复制粘贴以下命令（**把 `你的密码` 改成你自己的密码**）：

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

验证连接是否成功：

```bash
mysql -u patient_user -p'你的密码' patient_trend -e "SELECT '连接成功' AS status;"
```

如果出现 `连接成功` 四个字，数据库就没问题。

### 2.4 安装后端依赖

```bash
cd /opt/patient-trend/backend
python3.11 -m pip install -r requirements.txt
```

如果提示 `--break-system-packages` 错误，加上参数：

```bash
python3.11 -m pip install -r requirements.txt --break-system-packages
```

### 2.5 配置后端数据库连接

**文件位置**：项目根目录下的 `.env` 文件  
**完整路径**：`/opt/patient-trend/.env`

如果文件不存在，复制模板：

```bash
cd /opt/patient-trend
cp backend/.env.example .env
```

现在编辑它：

```bash
vi /opt/patient-trend/.env
```

按 `i` 键进入编辑模式，内容如下（**注意 4 处需要修改**）：

```ini
DATABASE_URL=mysql+aiomysql://patient_user:你的密码@localhost:3306/patient_trend?charset=utf8mb4
DATABASE_ECHO=false

# JWT 密钥：运行下方命令生成随机值，替换下面这个
SECRET_KEY=把这里换成你生成的密钥
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
DEBUG=false
```

**修改说明**：

| 位置 | 怎么改 | 示例 |
|------|--------|------|
| `patient_user` | 数据库用户名，保持不动 | `patient_user` |
| `你的密码` | 改成 2.3 里你设的实际密码 | `MyP@ssw0rd123` |
| `SECRET_KEY` | 运行下方命令生成，粘贴结果 | `a3f5b2c1d0e9f8...` |
| localhost | 如果数据库不在本机，改成 MySQL IP | `192.168.1.100` |

**生成 SECRET_KEY**：

```bash
# 终端运行这条命令，复制输出的一长串字符串
openssl rand -hex 32
```

> 密码里有 `!` `@` 等特殊字符？不用转义，直接填写即可。
> 
> 比如密码是 `abc@123!`，写成：`mysql+aiomysql://patient_user:abc@123!@localhost:3306/...`

### 2.6 启动后端

```bash
cd /opt/patient-trend

# 停止旧进程（如果有）
pkill -f uvicorn || true

# 启动后端（监听 35001 端口）
nohup python3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 35001 --reload > backend.log 2>&1 &

echo "后端 PID: $!"
```

验证后端是否正常：

```bash
# 查看日志
tail -5 backend.log
```

看到以下输出说明正常：

```
INFO:     Uvicorn running on http://0.0.0.0:35001
[migration] Executed 7 new statement(s) from 1 migration file(s)
```

```bash
# 用 curl 测试
curl http://localhost:35001/api/health
```

返回 `{"status":"ok",...}` 表示成功。

---

## 三、前端部署（Linux 服务器）

### 3.1 安装前端依赖

```bash
cd /opt/patient-trend/frontend
npm install
```

如果网络慢，切换国内镜像：

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### 3.2 配置前端 API 地址

前端有两个配置文件，**根据使用场景选一个改**：

| 文件 | 什么时候改 | 用途 |
|------|-----------|------|
| `.env.development` | 在 Linux 服务器上本地调试前端 | `npm run dev` 开发服务器 |
| `.env.production` | 打包 APP / 公网访问 | 构建后访问的后端地址 |

#### 3.2.1 开发服务器配置（在 Linux 服务器上）

```bash
# 如果文件被 .gitignore 忽略了，需要手动创建
vi /opt/patient-trend/frontend/.env.development
```

写入：

```ini
VITE_API_BASE_URL=/api
VITE_SERVER_URL=http://localhost:35001
```

说明：开发服务器会自动把 `/api` 请求转发到 `localhost:35001`，**不需要填后端地址**。

#### 3.2.2 生产环境配置（打包 APP / 公网访问时）

```bash
vi /opt/patient-trend/frontend/.env.production
```

写入（**把地址改成你服务器的真实地址和端口**）：

```ini
VITE_API_BASE_URL=http://你的服务器IP或域名:35001
```

比如你的服务器是 `www.021897.xyz:35001`：

```ini
VITE_API_BASE_URL=http://www.021897.xyz:35001
```

> **重要**：这两个 `.env.*` 文件已被 `.gitignore` 忽略，Git 不会上传。每次新部署或换服务器时都需要手动创建。

### 3.3 启动前端开发服务器

```bash
cd /opt/patient-trend/frontend
npm run dev
```

访问 `http://服务器IP:35000` 就能看到前端。

### 3.4 构建前端（用于打包 APP）

```bash
cd /opt/patient-trend/frontend

# 先用生产配置
vi /opt/patient-trend/frontend/.env.production   # 确认 VITE_API_BASE_URL 已填写
npm run build
```

构建完成后，`frontend/dist/` 目录包含静态文件，可用于生产部署或 APP 打包。

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

### 4.3 配置后端地址

APP 需要知道后端在哪。编辑 `.env.production` 文件：

找到文件：`frontend\.env.production`  
用记事本或 VS Code 打开，写入：

```ini
VITE_API_BASE_URL=http://你的服务器IP:35001
```

**比如**：
```ini
VITE_API_BASE_URL=http://www.021897.xyz:35001
```

> 如果服务器是内网 IP，比如 `192.168.1.100`，手机和电脑须在同一 WiFi 下才能访问。

### 4.4 检查 APP 名称

打开 `capacitor.config.ts`，确认以下内容：

```typescript
const config: CapacitorConfig = {
  appId: 'com.patient.trend',  // APP 包名（唯一标识）
  appName: '报告管理',           // APP 名称（显示在手机上）
  ...
}
```

如果想改名字，改 `appName` 即可。

### 4.5 构建并同步到 Android

```powershell
cd frontend

# 1. 构建前端
npm run build

# 2. 添加 Android 平台（首次执行需要）
npx cap add android

# 3. 同步前端构建产物到 Android 项目
npx cap sync android
```

### 4.6 用 Android Studio 打包 APK

```powershell
# 用 Android Studio 打开项目
npx cap open android
```

等待 Android Studio 打开项目并完成初始加载（左下角会显示 "Sync 成"）。

#### 6.1 方式一：调试版 APK（快速出包，用于测试）

1. 顶部菜单：**Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
2. 等待底部 Build 窗口显示 "BUILD SUCCESSFUL"
3. 弹出的 "Open in Explorer" 弹窗直接点击，APK 就在打开的文件夹里

APK 位置通常在：
```
frontend\android\app\build\outputs\apk\debug\app-debug.apk
```

把 APK 传到手机上，直接安装。

#### 6.2 方式二：正式版 APK（签名、可发应用市场）

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

### 5.1 更新后端代码

```bash
cd /opt/patient-trend
git pull

# 检查是否有新的 pip 依赖
cd backend && python3.11 -m pip install -r requirements.txt

# 重启后端
cd /opt/patient-trend
pkill -f uvicorn || true
nohup python3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 35001 --reload > backend.log 2>&1 &

# 查看启动日志
tail -5 backend.log
```

### 5.2 更新前端代码

```bash
cd /opt/patient-trend/frontend
git pull
npm install
npm run dev
```

### 5.3 查看后端日志

```bash
tail -f /opt/patient-trend/backend.log
# 按 Ctrl+C 退出
```

### 5.4 停止后端

```bash
pkill -f uvicorn
```

### 5.5 数据库备份

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
| 3 | 后端运行 | `curl http://localhost:35001/api/health` | `{"status":"ok",...}` |
| 4 | 前端运行 | 浏览器打开 `http://服务器IP:35000` | 看到登录页面 |
| 5 | 后端 API 文档 | 浏览器打开 `http://服务器IP:35001/api/docs` | Swagger 界面 |
| 6 | 数据库迁移 | `tail -5 backend.log` | 看到 `Executed 7 new statement(s)` |
| 7 | APP 安装 | APK 安装到手机打开 | 能看到登录页面 |
| 8 | APP 连接 | APP 登录成功 | 能看到首页数据 |
