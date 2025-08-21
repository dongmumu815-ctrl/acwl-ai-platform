# ACWL-AI 大模型管理平台

一个企业级的AI大模型管理和部署平台，支持模型的存储、部署、微调、监控和使用。

## 技术栈

### 后端
- **Python 3.9+**
- **FastAPI** - 现代、快速的Web框架
- **SQLAlchemy** - ORM框架
- **MySQL** - 主数据库
- **Redis** - 缓存和会话存储
- **Celery** - 异步任务队列
- **Docker** - 容器化部署

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全
- **Element Plus** - UI组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP客户端

## 项目结构

```
acwl-ai/
├── backend/                 # Python后端服务
│   ├── app/                # 应用核心代码
│   ├── requirements.txt    # Python依赖
│   ├── Dockerfile         # Docker配置
│   └── main.py           # 应用入口
├── frontend/              # Vue前端应用
│   ├── src/              # 源代码
│   ├── package.json      # Node.js依赖
│   └── vite.config.ts    # Vite配置
├── database/             # 数据库相关
│   └── schema.sql       # 数据库结构
├── docker-compose.yml   # Docker编排
└── README.md           # 项目说明
```

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Redis 6.0+

### 后端启动
```bash
cd backend
pip install -r requirements.txt

# 启动主API服务
uvicorn main:app --reload

# 启动调度器服务
python scheduler_service.py

# 启动执行器服务
python executor_service.py

# 启动执行器监控程序
python executor_monitor.py
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

## 功能特性

- 🤖 **模型管理** - 支持多种大模型的导入、存储和版本管理
- 🚀 **一键部署** - 支持vLLM、Ollama、HuggingFace等部署方式
- 📊 **资源监控** - 实时监控GPU、CPU、内存使用情况
- 🔧 **模型微调** - 支持LoRA、QLoRA等微调方法
- 🧠 **智能代理** - 基于大模型的Agent配置和管理
- 📚 **知识库** - RAG知识库构建和检索
- 🔐 **权限管理** - 完整的用户权限和API密钥管理
- 📈 **使用统计** - 详细的API调用和资源使用统计
- ⚡ **执行器集群** - 分布式任务执行和负载均衡
- 🔄 **任务调度** - 智能任务分配和状态管理
- 🛠️ **自动监控** - 执行器节点健康检查和自动清理

## 服务架构

### 核心服务
- **API服务** (`main.py`) - 提供RESTful API接口
- **调度器服务** (`scheduler_service.py`) - 任务调度和分配
- **执行器服务** (`executor_service.py`) - 任务执行节点
- **监控服务** (`executor_monitor.py`) - 节点健康监控和清理

### 数据库修复工具
- `fix_executor_status.py` - 修复执行器状态枚举值
- `fix_db_enum.py` - 数据库枚举类型修复
- `update_db_to_uppercase.py` - 状态值大小写标准化

### 启动脚本
- `start_cluster.bat` - 一键启动集群服务
- `start_executor_monitor.bat` - 启动监控程序

## 最新更新

### v1.2.0 (2025-08-08)
- ✅ 修复了执行器状态枚举值大小写问题
- ✅ 实现了执行器节点自动监控和清理
- ✅ 优化了集群服务的异常处理机制
- ✅ 添加了完整的服务启动脚本
- ✅ 修复了数据库枚举类型定义
- ✅ 改进了节点注册和心跳机制

## 许可证

MIT License