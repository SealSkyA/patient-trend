# Implementation Task List

Feature Name: patient-report-trend-analyzer
Updated: 2026-06-12

## Phase 1: 项目脚手架搭建

- [ ] Task 1.1: 创建后端项目结构（FastAPI + Python + 配置文件）
- [ ] Task 1.2: 创建前端项目结构（Vue 3 + TypeScript + Vite + Element Plus）
- [ ] Task 1.3: 配置数据库连接（MySQL + SQLAlchemy async + Alembic）

## Phase 2: 后端核心模块

- [ ] Task 2.1: 数据库模型定义（users, patients, reports, results, templates, template_items, metric_catalog）
- [ ] Task 2.2: Alembic 迁移脚本生成
- [ ] Task 2.3: 指标库 seed 数据脚本（预设指标和模板）
- [ ] Task 2.4: 认证模块（密码哈希、JWT 签发、JWT 验证中间件）
- [ ] Task 2.5: 用户注册/登录 API

## Phase 3: 后端业务 API

- [ ] Task 3.1: 患者管理 API（CRUD + 权限隔离）
- [ ] Task 3.2: 指标库查询 API + 归一化引擎
- [ ] Task 3.3: 自定义模板 CRUD API
- [ ] Task 3.4: 报告与检查结果 CRUD API（批量创建）
- [ ] Task 3.5: 趋势数据查询 API（聚合、分组、时间筛选、回归线计算）
- [ ] Task 3.6: 仪表板摘要 API（异常指标、最新报告、趋势预警）
- [ ] Task 3.7: 分享链接生成与只读访问 API

## Phase 4: 前端基础搭建

- [ ] Task 4.1: 前端项目初始化（路由、Pinia store、Axios 客户端）
- [ ] Task 4.2: 全局布局组件 + 导航栏 + 患者选择器
- [ ] Task 4.3: 登录/注册页面

## Phase 5: 前端核心页面

- [ ] Task 5.1: 个人仪表板页面（异常概览、最新报告、趋势预警）
- [ ] Task 5.2: 智能快捷录入页（指标搜索、模板选择、批量连续录入、移动端优化）
- [ ] Task 5.3: 趋势图详情页（ECharts 折线图、异常标记、回归线、时间筛选、悬停提示）
- [ ] Task 5.4: 报告库页面（时间轴布局、折叠展开、预览下载）
- [ ] Task 5.5: 模板管理页面（创建、编辑、删除自定义模板）
- [ ] Task 5.6: 患者管理页面（添加、编辑、删除患者档案）
- [ ] Task 5.7: 分享弹窗与只读分享页（临时链接访问）

## Phase 6: 联调与部署

- [ ] Task 6.1: 前后端联调验证（全部 API 端到端测试）
- [ ] Task 6.2: 生成详细部署文档
