# ACWL API Backend

这是ACWL API的后端服务，基于FastAPI框架开发。

## 项目结构

```
backend/
├── app/                    # 应用主目录
│   ├── api/               # API路由
│   │   └── v1/           # API v1版本
│   ├── core/             # 核心配置
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic模式
│   ├── services/         # 业务逻辑服务
│   └── utils/            # 工具函数
├── tests/                 # 测试文件
├── logs/                  # 日志文件
├── uploads/               # 上传文件存储
├── main.py               # 应用入口文件
├── requirements.txt      # Python依赖
├── database_schema.sql   # 数据库结构
├── init_database.py      # 数据库初始化脚本
└── .env.example         # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置相应的环境变量：

```bash
cp .env.example .env
```

### 3. 初始化数据库

```bash
python init_database.py
```

### 4. 启动服务

#### 方式一：使用启动脚本（推荐）

**Linux/macOS 环境：**
```bash
# 生产环境启动（使用Gunicorn + 配置文件）
python start_server.py

# 开发环境启动（使用Uvicorn，支持热重载）
python start_server.py --dev --reload

# 自定义配置启动
python start_server.py --port 8080 --workers 4 --config custom.conf.py
```

**Windows 环境：**
```bash
# 快速启动（固定配置，适合Windows）
python start.py

# 或使用跨平台脚本
python start_server.py
```

#### 方式二：直接使用框架

```bash
# 开发环境（支持热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产环境（使用Gunicorn）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 启动脚本说明

- **start_server.py**: 跨平台启动脚本，支持Linux/macOS/Windows，提供丰富的命令行参数
  - 支持开发模式和生产模式
  - 自动处理平台差异（如Windows的信号处理）
  - 支持自定义配置文件
  - 提供详细的日志输出

- **start.py**: Windows优化的快速启动脚本
  - 固定配置，快速启动
  - 适合Windows环境的简单部署
  - 使用预设的生产环境参数

## API文档

启动服务后，可以通过以下地址访问API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要功能模块

### 1. 认证鉴权 (`/api/v1/auth`)
- 用户登录
- Token验证
- 权限管理

### 2. 平台管理 (`/api/v1/customers`)
- 平台信息管理
- 客户状态控制

### 3. 批次管理 (`/api/v1/batches`)
- 数据批次创建
- 批次状态跟踪
- 批次处理

### 4. 数据管理 (`/api/v1/data`)
- 文件上传
- 数据处理
- 结果查询

### 5. 管理后台 (`/api/v1/admin`)
- 管理员管理
- 系统配置
- 统计信息

## 开发说明

### 代码规范
- 使用Python类型提示
- 遵循PEP 8代码风格
- 添加适当的文档字符串

### 数据库
- 使用SQLAlchemy ORM
- 支持MySQL/PostgreSQL
- 自动迁移管理

### 日志
- 结构化日志记录
- 多级别日志输出
- 日志文件轮转

### 测试
- 使用pytest测试框架
- 单元测试和集成测试
- 测试覆盖率报告

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t acwl-api .

# 运行容器
docker run -p 8000:8000 acwl-api
```

### 生产环境部署

#### Linux/macOS 环境（推荐）

**方式一：使用启动脚本**
```bash
# 使用默认配置启动
python start_server.py

# 自定义工作进程数
python start_server.py --workers 8

# 使用自定义配置文件
python start_server.py --config production.conf.py
```

**方式二：直接使用Gunicorn**
```bash
# 基本启动
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用配置文件
gunicorn --config gunicorn.conf.py main:app
```

#### Windows 环境

```bash
# 快速启动（推荐）
python start.py

# 或使用跨平台脚本
python start_server.py
```

#### 配合Nginx部署

建议在生产环境中使用Nginx作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 许可证

[添加许可证信息]