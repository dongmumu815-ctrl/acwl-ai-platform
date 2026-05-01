# ACWL AI Platform

企业级 AI 大模型管理与部署平台

[English](./README_EN.md) | 中文

---

## 📖 项目简介

ACWL AI Platform 是一个功能完善的企业级 AI 大模型管理和部署平台，提供从模型管理、Agent 构建、工作流编排到部署监控的完整解决方案。

平台支持多种主流 AI 大模型（如 LLaMA、Qwen、ChatGLM 等），提供可视化的模型服务配置、灵活的工作流引擎以及可扩展的 Agent 技能系统，帮助企业快速构建和部署 AI 应用。

---

## ✨ 核心特性

### 🤖 模型管理

- 多模型统一管理（支持 LLaMA、Qwen、ChatGLM 等）
- 模型服务配置与自动部署
- 模型版本控制与切换
- GPU 资源分配与管理

### 👥 Agent 构建

- 可视化 Agent 创建与配置
- 丰富的预置技能库（文档处理、代码生成、数据分析等）
- 灵活的指令集（Instruction Set）设计
- Agent 技能 API 直调用

### ⚙️ 工作流引擎

- 可视化工作流设计器
- 拖拽式节点编排
- 条件分支与循环控制
- 实时工作流执行监控

### 📊 数据集管理

- 多格式数据上传与处理（CSV、JSON、PDF、DOCX 等）
- 数据集版本管理
- 数据标注与清洗工具
- 与模型训练流程集成

### 🖥️ 服务器资源管理

- GPU/CPU 资源池管理
- 分布式执行器集群
- 自动化扩缩容
- 实时资源监控

### 🔐 权限与安全

- 基于角色的访问控制（RBAC）
- 细粒度权限管理
- 操作审计日志
- 数据加密传输

### 🗄️ 多数据库支持

- MySQL 主从架构
- 多业务数据库路由
- 动态数据库切换
- 数据源模板管理

### 📈 监控与告警

- 实时系统监控面板
- 任务执行状态追踪
- 异常告警通知
- 日志聚合与分析

---

## 🏗️ 技术栈

### 前端

| 技术          | 说明                       |
| ------------- | -------------------------- |
| Vue 3         | 渐进式 JavaScript 框架     |
| TypeScript    | 类型安全的 JavaScript 超集 |
| Element Plus  | 企业级 UI 组件库           |
| Vite          | 下一代前端构建工具         |
| Pinia         | Vue 状态管理               |
| Vue Router    | Vue 官方路由管理器         |
| ECharts       | 数据可视化图表库           |
| AntV X6       | 图形化流程编辑器           |
| Monaco Editor | 代码编辑器                 |
| Xterm.js      | 终端模拟器                 |

### 后端

| 技术         | 说明              |
| ------------ | ----------------- |
| Python 3.10+ | 主要编程语言      |
| FastAPI      | 高性能 Web 框架   |
| SQLAlchemy   | Python ORM 工具包 |
| Pydantic     | 数据验证库        |
| MySQL        | 关系型数据库      |
| Redis        | 缓存与消息队列    |
| Celery       | 分布式任务队列    |
| MinIO        | 对象存储服务      |
| Docker       | 容器化平台        |

---

## 📁 项目结构

```
acwl-ai-data/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── api/                # API 接口定义
│   │   ├── components/         # Vue 组件
│   │   ├── composables/        # 组合式函数
│   │   ├── directives/         # 自定义指令
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── utils/              # 工具函数
│   │   └── views/              # 页面视图
│   ├── public/                 # 静态资源
│   │   └── docs/               # 用户文档
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   ├── dependencies/  # 依赖注入
│   │   │   └── v1/
│   │   │       └── endpoints/  # 各业务模块接口
│   │   ├── core/              # 核心模块
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   ├── security.py    # 安全认证
│   │   │   └── middleware/     # 中间件
│   │   ├── crud/              # 数据增删改查
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务逻辑服务
│   │   └── utils/              # 工具函数
│   ├── .agents/               # Agent 技能系统
│   │   ├── skills-custom/     # 自定义技能
│   │   └── skills-system/     # 系统预置技能
│   ├── migrations/            # 数据库迁移
│   ├── scripts/               # 运维脚本
│   ├── Dockerfile
│   └── docker-compose-microservices.yml
│
├── .gitignore
└── README.md
```

---

## 🚀 快速开始

### 环境要求

| 依赖    | 版本要求       |
| ------- | -------------- |
| Node.js | >= 16.0.0      |
| npm     | >= 8.0.0       |
| Python  | >= 3.10        |
| MySQL   | >= 8.0         |
| Redis   | >= 6.0         |
| Docker  | >= 20.0 (可选) |

### 前置准备

1. **克隆项目**

```bash
git clone https://github.com/your-org/acwl-ai-data.git
cd acwl-ai-data
```

2. **配置数据库**

```bash
# 创建 MySQL 数据库
mysql -u root -p
CREATE DATABASE acwl-ai-data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **配置环境变量**

```bash
# 后端环境变量
cd backend
cp .env.example .env
# 编辑 .env 填入你的配置
```

### 安装与运行

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev

# 构建生产版本
npm run build
```

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

#### Docker 部署（推荐）

```bash
# 启动所有服务
docker-compose -f backend/docker-compose-microservices.yml up -d

# 查看服务状态
docker-compose -f backend/docker-compose-microservices.yml ps
```

---

## ⚙️ 配置说明

### 后端配置 (backend/.env)

```env
# 应用配置
PROJECT_NAME=ACWL-AI
VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# 服务器配置
HOST=0.0.0.0
PORT=8082

# 安全配置（生产环境必须修改）
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=acwl-ai-data

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# MinIO 配置（对象存储）
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
```

### 多数据库配置 (backend/multi_db_config.json)

平台支持多数据库路由配置，可按业务标签分流：

```json
{
  "databases": {
    "primary": {
      "name": "primary",
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "acwl-ai-data",
      "business_tags": ["primary", "main", "core"]
    },
    "analytics": {
      "name": "analytics",
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "analytics_db",
      "business_tags": ["analytics", "statistics"]
    }
  }
}
```

---

## 📚 API 文档

启动服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8082/docs
- **ReDoc**: http://localhost:8082/redoc
- **OpenAPI JSON**: http://localhost:8082/openapi.json

### 主要 API 模块

| 模块   | 说明         | 主要端点                  |
| ------ | ------------ | ------------------------- |
| 认证   | 用户登录注册 | `/api/v1/auth/*`        |
| 用户   | 用户管理     | `/api/v1/users/*`       |
| 模型   | AI 模型管理  | `/api/v1/models/*`      |
| Agent  | Agent 管理   | `/api/v1/agents/*`      |
| 工作流 | 工作流管理   | `/api/v1/workflows/*`   |
| 数据集 | 数据集管理   | `/api/v1/datasets/*`    |
| 服务器 | 资源管理     | `/api/v1/servers/*`     |
| 调度器 | 任务调度     | `/api/v1/schedulers/*`  |
| 部署   | 模型部署     | `/api/v1/deployments/*` |

---

## 🧩 Agent 技能系统

平台提供可扩展的 Agent 技能系统，支持自定义和系统预置技能。

### 技能目录结构

```
backend/.agents/
├── skills-custom/          # 自定义技能
│   ├── book-review/        # 图书评论技能
│   ├── kids-book-translator/  # 儿童图书翻译
│   └── book-pdf-meta-parser/   # PDF 元数据解析
│
└── skills-system/         # 系统预置技能
    ├── algorithmic-art/   # 算法艺术生成
    ├── brand-guidelines/   # 品牌规范
    ├── canvas-design/      # Canvas 设计
    ├── doc-coauthoring/    # 文档协作
    ├── docx/               # Word 文档处理
    ├── frontend-design/    # 前端设计
    ├── internal-comms/     # 内部沟通
    ├── mcp-builder/        # MCP 服务器构建
    ├── pdf/                # PDF 处理
    ├── pptx/               # PPT 处理
    ├── skill-creator/      # 技能创建器
    ├── slack-gif-creator/  # GIF 创建
    ├── theme-factory/      # 主题工厂
    ├── web-artifacts-builder/  # Web 构建
    ├── webapp-testing/     # Web 测试
    └── xlsx/               # Excel 处理
```

### 开发自定义技能

参考 [SKILL.md](./backend/.agents/skills-system/docx/SKILL.md) 了解技能开发规范。

---

## 🔧 运维脚本

项目提供丰富的运维脚本，位于 `backend/scripts/` 目录：

| 脚本                        | 说明               |
| --------------------------- | ------------------ |
| `check_cluster_status.py` | 检查集群状态       |
| `cluster_manager.py`      | 集群管理           |
| `init_harbor.py`          | 初始化 Harbor 仓库 |
| `generate_hosts.py`       | 生成主机配置       |
| `executor_monitor.py`     | 执行器监控         |
| `debug_*.py`              | 各类调试脚本       |

---

## 🗂️ 数据库迁移

数据库迁移文件位于 `backend/migrations/` 目录，按序号执行：

```bash
# 执行迁移（示例）
mysql -u root -p acwl-ai-data < backend/migrations/001_add_server_gpu_tables.sql
mysql -u root -p acwl-ai-data < backend/migrations/002_add_dataset_status_field.sql
# ... 以此类推
```

---

## 📊 监控面板

平台提供实时监控功能，包括：

- **系统概览**: 资源使用率、活跃用户、任务统计
- **服务器状态**: CPU、内存、GPU 监控
- **Agent 监控**: 请求量、响应时间、错误率
- **工作流监控**: 执行状态、耗时统计

---

## 🛡️ 安全说明

### 生产环境部署

1. **修改所有默认密钥和密码**
2. **启用 HTTPS**
3. **配置防火墙规则**
4. **启用 Redis 密码认证**
5. **定期备份数据库**
6. **开启审计日志**

### 权限控制

平台采用 RBAC 模型：

- **超级管理员**: 全部权限
- **管理员**: 大部分管理权限
- **普通用户**: 受限的功能权限
- **访客**: 只读权限

---

## 🤝 贡献指南

欢迎提交 Pull Request 或 Issue！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目基于 [Apache License 2.0](./LICENSE) 开源。

---

## 📞 联系方式

- dongmumu815@gmail.com

---

## 🙏 致谢

感谢所有为项目做出贡献的开发者！

## 👤 作者

GitHub: [@dongmumu815](https://github.com/yourusername)
