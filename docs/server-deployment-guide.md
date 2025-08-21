# 服务器管理与模型部署系统

## 系统概述

本系统实现了完整的AI模型部署管理功能，包括服务器资源管理、GPU资源分配、Docker容器化部署等核心功能。系统采用前后端分离架构，支持多服务器、多GPU的分布式部署。

## 核心功能

### 1. 服务器管理
- **服务器注册**: 添加和管理多台GPU服务器
- **状态监控**: 实时监控服务器在线状态、资源使用情况
- **SSH连接**: 支持SSH密钥认证，安全连接远程服务器
- **硬件信息**: 自动检测CPU、内存、磁盘、GPU等硬件配置
- **系统信息**: 监控操作系统、Docker、NVIDIA驱动版本

### 2. GPU资源管理
- **GPU发现**: 自动扫描和识别服务器上的GPU设备
- **资源分配**: 智能分配GPU资源给不同的部署任务
- **使用监控**: 实时监控GPU使用率、显存占用、温度等指标
- **可用性管理**: 动态管理GPU资源的可用状态

### 3. 模型部署
- **Docker部署**: 基于Docker容器的模型部署
- **多GPU支持**: 支持单个部署使用多个GPU资源
- **资源隔离**: 每个部署独立的资源配置和环境隔离
- **生命周期管理**: 支持部署的启动、停止、重启、删除操作
- **健康检查**: 自动监控部署状态和健康状况

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   后端API       │    │   数据库        │
│                 │    │                 │    │                 │
│ - 服务器管理    │◄──►│ - 服务器API     │◄──►│ - servers       │
│ - GPU资源管理   │    │ - GPU资源API    │    │ - gpu_resources │
│ - 部署管理      │    │ - 部署API       │    │ - deployments   │
│ - 监控面板      │    │ - 监控API       │    │ - server_metrics│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   部署服务      │
                       │                 │
                       │ - Docker管理    │
                       │ - SSH连接       │
                       │ - 资源分配      │
                       │ - 状态监控      │
                       └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GPU服务器1    │    │   GPU服务器2    │    │   GPU服务器N    │
│                 │    │                 │    │                 │
│ - Docker容器    │    │ - Docker容器    │    │ - Docker容器    │
│ - GPU资源       │    │ - GPU资源       │    │ - GPU资源       │
│ - 模型服务      │    │ - 模型服务      │    │ - 模型服务      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 数据库设计

### 核心表结构

1. **servers** - 服务器信息表
   - 存储服务器基本信息、连接配置、硬件规格
   - 支持状态管理和心跳检测

2. **gpu_resources** - GPU资源表
   - 记录每台服务器的GPU设备信息
   - 实时更新GPU使用状态和性能指标

3. **deployments** - 部署信息表
   - 存储模型部署的配置和状态
   - 关联服务器和GPU资源

4. **deployment_gpus** - 部署GPU关联表
   - 管理部署与GPU资源的多对多关系
   - 支持GPU显存限制配置

5. **server_metrics** - 服务器监控指标表
   - 记录服务器性能监控数据
   - 支持历史数据查询和趋势分析

## 部署流程

### 1. 服务器准备
```bash
# 安装Docker
sudo apt update
sudo apt install docker.io

# 安装NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install nvidia-docker2
sudo systemctl restart docker

# 配置SSH密钥认证
ssh-keygen -t rsa -b 4096
ssh-copy-id user@server-ip
```

### 2. 系统配置

#### 后端配置
```python
# app/core/config.py
class Settings:
    # 数据库配置
    DATABASE_URL = "sqlite:///./acwl.db"
    
    # SSH配置
    SSH_PRIVATE_KEY_PATH = "/path/to/ssh/private/key"
    SSH_CONNECTION_TIMEOUT = 30
    
    # Docker配置
    DOCKER_REGISTRY = "your-registry.com"
    DEFAULT_MODEL_IMAGE = "acwl-model:latest"
```

#### 前端配置
```typescript
// src/config/api.ts
export const API_BASE_URL = 'http://localhost:8000/api/v1'
export const WS_BASE_URL = 'ws://localhost:8000/ws'
```

### 3. 数据库初始化
```bash
# 运行迁移脚本
sqlite3 acwl.db < migrations/001_add_server_gpu_tables.sql
```

### 4. 启动服务
```bash
# 启动后端服务
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动前端服务
cd frontend
npm install
npm run dev
```

## 使用指南

### 1. 添加服务器
1. 进入「服务器管理」页面
2. 点击「添加服务器」按钮
3. 填写服务器信息：
   - 服务器名称
   - IP地址
   - SSH端口和用户名
   - 描述和标签
4. 点击「测试连接」验证连接
5. 保存服务器配置

### 2. 扫描GPU资源
1. 在服务器列表中选择目标服务器
2. 点击「扫描GPU」按钮
3. 系统自动检测并添加GPU资源
4. 查看GPU详细信息和状态

### 3. 创建部署
1. 进入「部署管理」页面
2. 点击「创建部署」按钮
3. 配置部署信息：
   - 部署名称和描述
   - 选择模型
   - 选择目标服务器
   - 分配GPU资源
   - 配置运行参数
4. 提交创建部署
5. 监控部署状态

### 4. 管理部署
- **启动/停止**: 控制部署的运行状态
- **重启**: 重新启动部署服务
- **扩缩容**: 调整资源分配
- **查看日志**: 监控部署运行日志
- **监控指标**: 查看性能监控数据

## API接口

### 服务器管理API
```
GET    /api/v1/servers              # 获取服务器列表
POST   /api/v1/servers              # 创建服务器
GET    /api/v1/servers/{id}         # 获取服务器详情
PUT    /api/v1/servers/{id}         # 更新服务器
DELETE /api/v1/servers/{id}         # 删除服务器
POST   /api/v1/servers/{id}/test    # 测试服务器连接
POST   /api/v1/servers/{id}/scan-gpu # 扫描GPU资源
```

### GPU资源API
```
GET    /api/v1/servers/{id}/gpus    # 获取服务器GPU列表
PUT    /api/v1/gpus/{id}            # 更新GPU信息
```

### 部署管理API
```
GET    /api/v1/deployments          # 获取部署列表
POST   /api/v1/deployments          # 创建部署
GET    /api/v1/deployments/{id}     # 获取部署详情
PUT    /api/v1/deployments/{id}     # 更新部署
DELETE /api/v1/deployments/{id}     # 删除部署
POST   /api/v1/deployments/{id}/start   # 启动部署
POST   /api/v1/deployments/{id}/stop    # 停止部署
POST   /api/v1/deployments/{id}/restart # 重启部署
```

## 监控和运维

### 1. 系统监控
- 服务器状态监控
- GPU使用率监控
- 部署健康状态监控
- 资源使用趋势分析

### 2. 日志管理
- 部署运行日志
- 系统操作日志
- 错误日志收集
- 日志轮转和清理

### 3. 告警机制
- 服务器离线告警
- GPU温度过高告警
- 部署异常告警
- 资源不足告警

## 安全考虑

### 1. 网络安全
- SSH密钥认证
- API访问控制
- 网络隔离
- 防火墙配置

### 2. 数据安全
- 敏感信息加密
- 访问权限控制
- 操作审计日志
- 数据备份策略

### 3. 容器安全
- 镜像安全扫描
- 运行时安全监控
- 资源限制
- 网络隔离

## 故障排除

### 常见问题

1. **服务器连接失败**
   - 检查网络连通性
   - 验证SSH配置
   - 确认防火墙设置

2. **GPU检测失败**
   - 检查NVIDIA驱动安装
   - 验证nvidia-docker配置
   - 确认GPU设备权限

3. **部署启动失败**
   - 检查Docker镜像
   - 验证GPU资源可用性
   - 查看部署日志

4. **性能问题**
   - 监控资源使用情况
   - 检查网络带宽
   - 优化容器配置

### 日志位置
- 后端日志: `/var/log/acwl/backend.log`
- 部署日志: `/var/log/acwl/deployments/`
- Docker日志: `docker logs <container_name>`

## 扩展开发

### 1. 添加新的部署类型
```python
# 在 DeploymentService 中添加新的部署方法
async def _execute_k8s_deployment(self, deployment, server, gpu_associations):
    # Kubernetes部署逻辑
    pass
```

### 2. 集成监控系统
```python
# 添加Prometheus指标收集
from prometheus_client import Counter, Histogram, Gauge

deployment_counter = Counter('deployments_total', 'Total deployments')
gpu_usage_gauge = Gauge('gpu_usage_percent', 'GPU usage percentage')
```

### 3. 扩展前端功能
```vue
<!-- 添加新的监控图表组件 -->
<template>
  <div class="monitoring-dashboard">
    <gpu-usage-chart :data="gpuData" />
    <deployment-metrics :deployments="deployments" />
  </div>
</template>
```

## 版本更新

### v1.0.0 (当前版本)
- 基础服务器管理功能
- GPU资源管理
- Docker部署支持
- 基础监控功能

### 计划功能
- Kubernetes部署支持
- 自动扩缩容
- 高级监控和告警
- 多租户支持
- API网关集成

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request
5. 代码审查和合并

## 许可证

本项目采用MIT许可证，详见LICENSE文件。