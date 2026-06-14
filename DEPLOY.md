# 患者检查报告趋势分析系统 - 部署手册（openEuler 22.03）

## 一、系统概述

患者检查报告趋势分析系统是一个面向个人和家庭的数字健康管理 Web 应用。

| 项目 | 信息 |
|------|------|
| 前端端口 | **35000** |
| 后端端口 | **35001** |
| 前端框架 | Vue 3 + TypeScript + Vite + Element Plus + ECharts + Pinia |
| 后端框架 | Python 3.11+ + FastAPI + SQLAlchemy (async) + Pydantic |
| 数据库 | MySQL 8.0+ (utf8mb4) |
| 运行环境 | openEuler 22.03 LTS SP1 / openEuler 22.03 |

---

## 二、环境安装（全新系统首次部署）

### 2.1 更新系统包

```bash
sudo dnf update -y
```

### 2.2 安装 Node.js 20.x

```bash
# 安装 Node.js 20（使用 NodeSource）
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -

# 安装 Node.js
sudo dnf install -y nodejs

# 验证安装
node -v    # 应显示 v20.x.x
npm -v     # 应显示 10.x.x
```

**备选方案：使用 nvm 安装**

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# 安装 Node.js 20
nvm install 20
nvm use 20
nvm alias default 20
```

### 2.3 安装 Python 3.11+

openEuler 22.03 默认可能包含 Python 3.9，需要手动安装 Python 3.11：

```bash
# 安装 Python 3.11 及相关开发工具
sudo dnf install -y python3.11 python3.11-pip python3.11-devel python3.11-setuptools

# 如果没有 python3.11，尝试安装 python311
sudo dnf install -y python311 python311-pip python311-devel

# 验证安装
python3.11 --version  # 或 python311 --version
pip3.11 --version     # 或 pip311 --version
```

**备选方案：从源码编译 Python 3.11**

```bash
# 安装编译依赖
sudo dnf install -y gcc gcc-c++ make zlib-devel bzip2-devel \
    openssl-devel ncurses-devel sqlite-devel readline-devel \
    tk-devel gdbm-devel db4-devel libpcap-devel xz-devel libffi-devel

# 下载源码
cd /tmp
curl -O https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xzf Python-3.11.9.tgz
cd Python-3.11.9

# 编译安装
./configure --prefix=/usr/local/python3.11 --enable-optimizations
make -j$(nproc)
sudo make install

# 创建软链接
sudo ln -sf /usr/local/python3.11/bin/python3.11 /usr/bin/python3.11
sudo ln -sf /usr/local/python3.11/bin/pip3.11 /usr/bin/pip3.11

# 验证
python3.11 --version
```

### 2.4 安装 Git

```bash
sudo dnf install -y git
```

### 2.5 安装其他工具

```bash
# 安装 wget、curl 等工具
sudo dnf install -y wget curl unzip tar

# 安装编译工具（可选，用于安装某些 Python 依赖）
sudo dnf groupinstall -y "Development Tools"
```

---

## 三、项目部署

### 3.1 克隆代码

```bash
# 进入工作目录
cd /workspace

# 克隆项目（如果是新部署）
git clone <项目仓库地址> /workspace

# 或拉取最新代码（如果已存在）
cd /workspace && git pull
```

### 3.2 创建数据库

```bash
# 登录 MySQL
mysql -u root -p
```

在 MySQL 命令行中执行：

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS patient_trend
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- 创建用户（替换 your_password 为实际密码，建议至少 12 位）
CREATE USER IF NOT EXISTS 'patient_user'@'localhost' 
  IDENTIFIED BY 'your_secure_password_here';

-- 授予权限
GRANT ALL PRIVILEGES ON patient_trend.* TO 'patient_user'@'localhost';
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

验证连接：

```bash
mysql -u patient_user -p'your_secure_password_here' patient_trend -e "SELECT '连接成功' AS status;"
```

### 3.3 安装后端依赖

```bash
cd /workspace/backend

# 使用 Python 3.11 安装依赖
python3.11 -m pip install -r requirements.txt
```

如果遇到权限问题：

```bash
# openEuler 可能需要添加此参数
python3.11 -m pip install -r requirements.txt --break-system-packages
```

### 3.4 安装前端依赖

```bash
cd /workspace/frontend

# 安装 Node.js 依赖
npm install
```

如果网络较慢，可以使用国内镜像：

```bash
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
npm install
```

---

## 四、配置文件设置

### 4.1 后端环境变量

```bash
# 复制环境变量配置文件
cp /workspace/backend/.env.example /workspace/backend/.env

# 编辑配置（使用 vi 或 nano）
vi /workspace/backend/.env
```

**配置内容说明**：

```ini
# ===== 数据库配置 =====
DATABASE_URL=mysql+aiomysql://patient_user:你的密码@localhost:3306/patient_trend?charset=utf8mb4
DATABASE_ECHO=false

# ===== JWT 安全配置 =====
SECRET_KEY=你的 JWT 密钥（必须修改）
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# ===== 应用配置 =====
DEBUG=false
```

| 变量名 | 说明 | 必填 | 示例 |
|--------|------|------|------|
| `DATABASE_URL` | MySQL 连接字符串 | ✅ | `mysql+aiomysql://user:pass@localhost:3306/db` |
| `SECRET_KEY` | JWT 签名密钥 | ✅ | 使用下方命令生成 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期（分钟） | 可选 | `10080` (7 天) |
| `DEBUG` | 调试模式 | 可选 | `false` |

### 4.2 生成 JWT 密钥

```bash
# 生成随机密钥（32 字节）
openssl rand -hex 32

# 将输出结果复制到 .env 文件的 SECRET_KEY
```

### 4.3 配置数据库密码

将 `.env` 文件中的数据库密码修改为实际设置的密码：

```ini
DATABASE_URL=mysql+aiomysql://patient_user:你的实际密码@localhost:3306/patient_trend?charset=utf8mb4
```

---

## 五、启动服务

### 5.1 方式一：一键启动脚本（推荐）

```bash
chmod +x /workspace/start.sh
/workspace/start.sh
```

脚本会自动完成：
- 检查数据库连接
- 启动后端服务（端口 35001）
- 启动前端服务（端口 35000）

### 5.2 方式二：手动启动

#### 启动后端

```bash
cd /workspace/backend
nohup python3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 35001 > backend.log 2>&1 &
echo $! > backend.pid
```

#### 启动前端

```bash
cd /workspace/frontend
nohup npm run dev -- --host 0.0.0.0 --port 35000 > frontend.log 2>&1 &
echo $! > frontend.pid
```

### 5.3 方式三：systemd 开机自启动（生产环境推荐）

openEuler 使用 systemd 作为初始化系统，可以创建服务实现开机自启。

#### 创建后端服务

```bash
sudo tee /etc/systemd/system/patient-backend.service << 'EOF'
[Unit]
Description=患者检查报告趋势分析 - 后端服务
After=network.target mysqld.service

[Service]
Type=simple
WorkingDirectory=/workspace/backend
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 35001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

#### 创建前端服务

```bash
sudo tee /etc/systemd/system/patient-frontend.service << 'EOF'
[Unit]
Description=患者检查报告趋势分析 - 前端服务
After=network.target patient-backend.service

[Service]
Type=simple
WorkingDirectory=/workspace/frontend
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 35000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

#### 启用服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable patient-backend
sudo systemctl enable patient-frontend

# 启动服务
sudo systemctl start patient-backend
sudo systemctl start patient-frontend

# 查看状态
sudo systemctl status patient-backend
sudo systemctl status patient-frontend
```

---

## 六、服务验证

### 6.1 检查服务状态

```bash
# systemd 方式启动
sudo systemctl status patient-backend
sudo systemctl status patient-frontend

# 或 nohup 方式启动
ps aux | grep -E 'uvicorn|npm run dev' | grep -v grep
```

### 6.2 检查端口

```bash
# 查看端口占用
ss -tlnp | grep -E '35000|35001'
# 或使用 netstat
netstat -tlnp | grep -E '35000|35001'
```

### 6.3 访问服务

| 服务 | 地址 | 预期结果 |
|------|------|---------|
| 前端首页 | `http://localhost:35000` | 登录/注册页面 |
| 后端健康检查 | `http://localhost:35001/api/health` | `{"status":"ok",...}` |
| 后端 API 文档 | `http://localhost:35001/api/docs` | Swagger UI |

### 6.4 检查数据库表

```bash
mysql -u patient_user -p'你的密码' patient_trend -e "SHOW TABLES;"
```

预期表列表：
- `users` - 用户表
- `patients` - 患者表
- `reports` - 报告表
- `results` - 检查结果表
- `templates` - 模板表
- `template_items` - 模板指标表
- `share_tokens` - 分享令牌表
- `medication_records` - 用药记录表
- `medication_items` - 用药项目表

---

## 七、常用运维操作

### 7.1 启动/停止/重启

```bash
# systemd 方式
sudo systemctl start patient-backend
sudo systemctl stop patient-backend
sudo systemctl restart patient-backend

# nohup 方式
cd /workspace
pkill -f "uvicorn backend.main:app"
pkill -f "npm run dev"
```

### 7.2 查看日志

```bash
# systemd 方式
sudo journalctl -u patient-backend -f --no-pager
sudo journalctl -u patient-frontend -f --no-pager

# nohup 方式
tail -f /workspace/backend/backend.log
tail -f /workspace/frontend/frontend.log
```

### 7.3 更新代码

```bash
cd /workspace
git pull

# 后端
cd /workspace/backend
python3.11 -m pip install -r requirements.txt

# 前端
cd /workspace/frontend
npm install

# 重启服务
sudo systemctl restart patient-backend patient-frontend
```

### 7.4 备份数据库

```bash
# 备份
mysqldump -u patient_user -p'你的密码' patient_trend | gzip > /backup/patient_trend_$(date +%Y%m%d_%H%M%S).sql.gz

# 恢复
zcat /backup/patient_trend_yyyyMMdd_HHmmss.sql.gz | mysql -u patient_user -p'你的密码' patient_trend
```

---

## 八、常见问题排查

### 8.1 后端无法启动

```bash
# 检查 Python 依赖
cd /workspace/backend && python3.11 -m pip install -r requirements.txt

# 检查数据库连接
python3.11 -c "
from sqlalchemy import create_engine
engine = create_engine('你的 DATABASE_URL')
conn = engine.connect()
print('数据库连接成功')
"

# 查看日志
tail -f /workspace/backend/backend.log
```

### 8.2 前端页面空白

```bash
# 检查前端构建
cd /workspace/frontend
npm run build

# 查看日志
tail -f /workspace/frontend/frontend.log
```

### 8.3 端口被占用

```bash
# 查找占用进程
sudo lsof -i :35000
sudo lsof -i :35001

# 杀死进程
sudo kill -9 <PID>
```

### 8.4 数据库连接失败

```bash
# 检查 MySQL 服务
sudo systemctl status mysqld

# 测试连接
mysql -u patient_user -p'你的密码' patient_trend -e "SELECT 1;"

# 检查权限
mysql -u root -p -e "SHOW GRANTS FOR 'patient_user'@'localhost';"
```

### 8.5 npm 安装依赖失败

```bash
# 清空缓存
npm cache clean --force

# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 删除 node_modules 重新安装
rm -rf node_modules package-lock.json
npm install
```

### 8.6 Python 模块导入错误

```bash
# 确保使用正确的 Python 版本
which python3.11

# 重新安装依赖
python3.11 -m pip install -r requirements.txt --force-reinstall
```

---

## 九、安全加固

### 9.1 防火墙配置（firewalld）

openEuler 默认使用 firewalld 作为防火墙：

```bash
# 安装 firewalld（如果未安装）
sudo dnf install -y firewalld

# 启动服务
sudo systemctl start firewalld
sudo systemctl enable firewalld

# 允许 SSH 和业务端口
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=35000/tcp

# 只允许内网访问后端（可选）
# sudo firewall-cmd --permanent --add-port=35001/tcp --add-source=127.0.0.1/32

# 重载配置
sudo firewall-cmd --reload

# 查看规则
sudo firewall-cmd --list-all
```

### 9.2 SELinux 配置

如果启用 SELinux，可能需要调整策略：

```bash
# 查看 SELinux 状态
getenforce

# 如果为 Enforcing，可以临时设置为 Permissive 测试
sudo setenforce 0

# 或添加 SELinux 策略允许端口
sudo semanage port -a -t http_port_t -p tcp 35000
sudo semanage port -a -t http_port_t -p tcp 35001
```

### 9.3 MySQL 安全配置

```bash
# 运行安全配置脚本
mysql_secure_installation
```

根据提示：
- 设置 root 密码
- 删除匿名用户
- 禁止 root 远程登录
- 删除测试数据库

### 9.4 定期备份

```bash
# 创建备份脚本
sudo tee /usr/local/bin/backup-patient-trend.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backup
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u patient_user -p'你的密码' patient_trend | gzip > $BACKUP_DIR/patient_trend_$DATE.sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

sudo chmod +x /usr/local/bin/backup-patient-trend.sh

# 添加定时任务（每天凌晨 2 点）
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-patient-trend.sh") | crontab -
```

---

## 十、系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│              用户 PC (openEuler 22.03)                      │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │   浏览器      │────>│  前端服务     │                     │
│  │              │     │  Vite+Vue 3  │                     │
│  │              │     │  Port 35000  │                     │
│  └──────────────┘     └───────┬──────┘                     │
│                                │ API 请求                   │
│                                ▼                          │
│                       ┌──────────────┐                     │
│                       │  后端服务     │                     │
│                       │  FastAPI     │                     │
│                       │  Port 35001  │                     │
│                       └───────┬──────┘                     │
│                               │                             │
│              ┌────────────────┼────────────────┐            │
│              ▼                ▼                ▼            │
│       ┌──────────┐    ┌──────────┐    ┌──────────┐        │
│       │  MySQL   │    │ uploads/ │    │   logs/  │        │
│       │  Port3306│    │  文件存储 │    │  日志文件 │        │
│       └──────────┘    └──────────┘    └──────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 十一、技术栈详情

| 组件 | 技术选型 | 版本 |
|------|---------|------|
| 前端 | Vue 3 + TypeScript | 3.4+ |
| UI 框架 | Element Plus | 2.x |
| 图表 | ECharts | 5.x |
| 状态管理 | Pinia | 2.x |
| 构建工具 | Vite | 5.x |
| 后端 | FastAPI | 0.100+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| 数据验证 | Pydantic | 2.x |
| 数据库 | MySQL | 8.0+ |
| 认证 | JWT (python-jose) | 3.x |

---

## 十二、openEuler 特定注意事项

### 12.1 软件源配置

如果默认源下载较慢，可以切换到国内镜像：

```bash
# 备份原配置
sudo cp /etc/yum.repos.d/openEuler.repo /etc/yum.repos.d/openEuler.repo.bak

# 使用阿里云镜像
sudo sed -i 's|repo.openeuler.org|mirrors.aliyun.com/openeuler|g' /etc/yum.repos.d/openEuler.repo

# 刷新缓存
sudo dnf makecache
```

### 12.2 时间同步

```bash
# 安装 chrony
sudo dnf install -y chrony

# 启动服务
sudo systemctl start chronyd
sudo systemctl enable chronyd

# 检查同步状态
chronyc sources -v
```

### 12.3 系统资源限制

如果服务运行中遇到资源限制，可以调整：

```bash
# 查看当前限制
ulimit -a

# 临时增加文件描述符限制
ulimit -n 65536

# 永久修改，编辑 /etc/security/limits.conf
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

---

## 十三、联系与支持

如遇部署问题，请检查：
1. 日志文件（`journalctl` 或 `*.log`）
2. 数据库连接配置
3. 端口占用情况
4. 依赖安装完整性
5. 防火墙和 SELinux 设置

建议保存此文档，便于后续运维参考。

---

## 附录：快速部署命令汇总

```bash
# 1. 系统更新
sudo dnf update -y

# 2. 安装 Node.js
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# 3. 安装 Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# 4. 安装其他工具
sudo dnf install -y git wget curl

# 5. 创建数据库（登录 MySQL 后执行）
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS patient_trend DEFAULT CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'patient_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON patient_trend.* TO 'patient_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# 6. 安装后端依赖
cd /workspace/backend && python3.11 -m pip install -r requirements.txt

# 7. 安装前端依赖
cd /workspace/frontend && npm install

# 8. 配置环境变量
cp /workspace/backend/.env.example /workspace/backend/.env
vi /workspace/backend/.env  # 修改数据库密码和 SECRET_KEY

# 9. 启动服务
/workspace/start.sh

# 10. 验证
curl http://localhost:35001/api/health
```

部署完成后访问：
- 前端：http://localhost:35000
- 后端 API 文档：http://localhost:35001/api/docs
