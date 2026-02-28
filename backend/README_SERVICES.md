# ACWL AI 数据平台服务启动指南

本文档介绍如何手动启动 ACWL AI 数据平台的各个微服务组件。

## 目录
- [服务列表](#服务列表)
- [环境要求](#环境要求)
- [启动方式](#启动方式)
  - [使用集群管理器 (推荐)](#使用集群管理器-推荐)
  - [手动启动各个服务](#手动启动各个服务)
- [停止服务](#停止服务)

## 服务列表

| 服务名称 | 描述 | 默认端口 | 脚本文件 |
| --- | --- | --- | --- |
| **主应用** | 后端 API 服务，提供核心业务接口 | 8000 | `main.py` |
| **调度器 (Scheduler)** | 负责工作流调度、Leader 选举 | 6789 (可配置) | `scheduler_service.py` |
| **执行器 (Executor)** | 负责具体任务执行 (Python/Shell/SQL) | 9876 (可配置) | `executor_service.py` |
| **执行器监控 (Monitor)** | 监控执行器健康状态，清理离线节点 | - | `executor_monitor.py` |

## 环境要求

- Python 3.9+
- 依赖包已安装 (`pip install -r requirements.txt`)
- 数据库 (MySQL) 已启动并配置正确

## 启动方式

所有命令均需在 `backend` 目录下执行：
```powershell
cd d:\works\codes\acwl-ai-data\backend
```

### 使用集群管理器 (推荐)

我们提供了一个 `cluster_manager.py` 脚本，可以批量启动和管理服务。

1. **启动所有服务 (3个调度器 + 3个执行器 + 监控)**
   ```powershell
   python cluster_manager.py start --all
   ```

2. **仅启动调度器集群**
   ```powershell
   python cluster_manager.py start --schedulers 3
   ```

3. **仅启动执行器集群**
   ```powershell
   python cluster_manager.py start --executors 3
   ```

4. **仅启动监控服务**
   ```powershell
   python cluster_manager.py start --monitor
   ```

### 手动启动各个服务

如果您需要更精细的控制，可以手动启动每个服务。建议在不同的终端窗口中运行。

#### 1. 启动调度器 (Scheduler)

```powershell
python scheduler_service.py --node-id scheduler-001 --host-ip 127.0.0.1 --port 6789
```
*参数说明：*
- `--node-id`: 节点唯一标识
- `--host-ip`: 绑定 IP (建议本地开发使用 127.0.0.1)
- `--port`: 服务端口

#### 2. 启动执行器 (Executor)

```powershell
python executor_service.py --node-id executor-001 --host-ip 127.0.0.1 --port 9876
```
*参数说明：*
- `--node-id`: 节点唯一标识
- `--host-ip`: 绑定 IP
- `--port`: 服务端口

#### 3. 启动执行器监控 (Monitor)

```powershell
python executor_monitor.py
```
*说明：监控服务通常只需要启动一个实例。*

#### 4. 启动主应用 (Main API)

```powershell
python main.py
```

## 停止服务

### 使用集群管理器停止所有服务

```powershell
python cluster_manager.py stop --all
```

### 手动停止 (PowerShell)

如果需要强制杀死所有相关 Python 进程：

```powershell
Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like "*executor_service.py*" -or $_.CommandLine -like "*scheduler_service.py*" -or $_.CommandLine -like "*executor_monitor.py*" -or $_.CommandLine -like "*cluster_manager.py*"} | Stop-Process -Force
```
