# Doris集成指南

本文档详细介绍如何在ACWL API系统中集成Apache Doris，实现高性能的访问日志存储和分析。

## 目录

- [概述](#概述)
- [优势](#优势)
- [系统架构](#系统架构)
- [安装配置](#安装配置)
- [使用方法](#使用方法)
- [性能优化](#性能优化)
- [监控运维](#监控运维)
- [故障排除](#故障排除)

## 概述

Apache Doris是一个现代化的MPP分析型数据库产品，具有以下特点：

- **高性能**：列式存储，向量化执行引擎
- **实时性**：支持实时数据导入和查询
- **易用性**：兼容MySQL协议，学习成本低
- **扩展性**：支持水平扩展，PB级数据处理能力

## 优势

### 相比传统文件日志

| 特性 | 文件日志 | Doris |
|------|---------|-------|
| **查询性能** | 慢，需要全文扫描 | 快，列式存储+索引 |
| **存储压缩** | 低压缩比 | 高压缩比（5-10倍） |
| **并发查询** | 受限于磁盘IO | 支持高并发 |
| **数据分析** | 需要额外工具 | 内置SQL分析 |
| **实时性** | 延迟高 | 准实时 |
| **扩展性** | 单机限制 | 水平扩展 |

### 相比MySQL

| 特性 | MySQL | Doris |
|------|-------|-------|
| **分析查询** | 慢，不适合OLAP | 快，专为分析设计 |
| **数据压缩** | 压缩比低 | 压缩比高 |
| **写入性能** | 单条写入快 | 批量写入快 |
| **存储成本** | 高 | 低 |
| **维护成本** | 高 | 低 |

## 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API请求       │    │   访问日志中间件    │    │   本地文件日志    │
│                 │───▶│                  │───▶│                 │
│ FastAPI应用     │    │ AccessLogging    │    │ app_access.log  │
└─────────────────┘    │ Middleware       │    └─────────────────┘
                       │                  │
                       │                  │    ┌─────────────────┐
                       │                  │───▶│   Doris集群     │
                       └──────────────────┘    │                 │
                                               │ • 批量写入       │
                                               │ • 实时查询       │
                                               │ • 数据压缩       │
                                               └─────────────────┘
```

### 数据流程

1. **请求处理**：API请求通过FastAPI应用处理
2. **中间件拦截**：访问日志中间件自动拦截所有请求
3. **数据提取**：提取请求和响应的详细信息
4. **双重记录**：
   - 同步记录到本地文件（保证可靠性）
   - 异步批量写入Doris（提供分析能力）
5. **批量优化**：使用队列和批量写入提高性能

## 安装配置

### 1. 安装依赖

```bash
# 安装Python依赖
pip install pymysql requests

# 或者更新requirements.txt
echo "pymysql>=1.0.2" >> requirements.txt
echo "requests>=2.28.0" >> requirements.txt
pip install -r requirements.txt
```

### 2. 配置Doris

复制配置文件模板：

```bash
cp .env.doris.example .env
```

编辑`.env`文件，配置Doris连接信息：

```env
# 启用Doris
DORIS_ENABLED=true

# Doris集群配置
DORIS_HOST=your-doris-host
DORIS_HTTP_PORT=8030
DORIS_QUERY_PORT=9030
DORIS_USER=root
DORIS_PASSWORD=your-password

# 数据库配置
DORIS_DATABASE=acwl_logs
DORIS_ACCESS_LOG_TABLE=api_access_logs

# 性能配置
DORIS_BATCH_SIZE=100
DORIS_FLUSH_INTERVAL=30
```

### 3. 初始化数据库

运行初始化脚本：

```bash
cd backend
python init_doris.py
```

脚本会自动：
- 测试Doris连接
- 创建数据库和表
- 验证表结构
- 执行数据插入测试

### 4. 集成中间件

在`main.py`中添加访问日志中间件：

```python
from app.middleware.access_logging import AccessLoggingMiddleware

# 添加访问日志中间件
app.add_middleware(
    AccessLoggingMiddleware,
    exclude_paths=["/health", "/metrics", "/docs", "/redoc"]
)
```

## 使用方法

### 1. 启动应用

```bash
# 启动应用
python main.py

# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 访问API测试

```bash
# 发送测试请求
curl -X GET "http://localhost:8000/api/v1/health"
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
```

### 3. 查询访问日志

#### 使用Python API

```python
from app.core.doris_client import get_doris_client

client = get_doris_client()

# 查询最近的访问记录
results = client.query_access_logs(limit=100)

# 按时间范围查询
results = client.query_access_logs(
    start_time="2024-01-01 00:00:00",
    end_time="2024-01-02 00:00:00",
    limit=1000
)

# 按HTTP方法查询
results = client.query_access_logs(method="POST", limit=50)

# 按状态码查询
results = client.query_access_logs(status_code=500, limit=50)
```

#### 使用SQL查询

```sql
-- 连接到Doris
mysql -h your-doris-host -P 9030 -u root -p

-- 使用数据库
USE acwl_logs;

-- 查询最近的访问记录
SELECT * FROM api_access_logs 
ORDER BY timestamp DESC 
LIMIT 100;

-- 统计每小时的请求量
SELECT 
    DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as hour,
    COUNT(*) as request_count,
    AVG(response_time) as avg_response_time
FROM api_access_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY hour
ORDER BY hour;

-- 统计状态码分布
SELECT 
    status_code,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM api_access_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY status_code
ORDER BY count DESC;

-- 查找慢请求
SELECT 
    timestamp,
    method,
    url,
    status_code,
    response_time,
    client_ip,
    user_id
FROM api_access_logs 
WHERE response_time > 1.0
ORDER BY response_time DESC
LIMIT 50;

-- 统计API使用情况
SELECT 
    url,
    COUNT(*) as request_count,
    AVG(response_time) as avg_response_time,
    MAX(response_time) as max_response_time
FROM api_access_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
GROUP BY url
ORDER BY request_count DESC
LIMIT 20;
```

## 性能优化

### 1. 批量写入优化

```python
# 在.env中调整批量参数
DORIS_BATCH_SIZE=500        # 增加批量大小
DORIS_FLUSH_INTERVAL=10     # 减少刷新间隔
```

### 2. 表结构优化

```sql
-- 创建分区表（按日期分区）
CREATE TABLE api_access_logs_partitioned (
    `timestamp` DATETIME NOT NULL,
    `method` VARCHAR(10) NOT NULL,
    `url` VARCHAR(2048) NOT NULL,
    -- 其他字段...
)
DUPLICATE KEY(`timestamp`, `method`, `url`)
PARTITION BY RANGE(`timestamp`)
(
    PARTITION p20240101 VALUES LESS THAN ("2024-01-02"),
    PARTITION p20240102 VALUES LESS THAN ("2024-01-03")
    -- 自动分区管理
)
DISTRIBUTED BY HASH(`timestamp`) BUCKETS 32;
```

### 3. 索引优化

```sql
-- 创建Bloom Filter索引
ALTER TABLE api_access_logs 
SET ("bloom_filter_columns" = "url,client_ip,user_id");

-- 创建倒排索引
ALTER TABLE api_access_logs 
ADD INDEX idx_url (url) USING INVERTED;
```

### 4. 压缩优化

```sql
-- 设置压缩算法
ALTER TABLE api_access_logs 
SET ("compression" = "ZSTD");
```

## 监控运维

### 1. 监控指标

```python
# 创建监控脚本
import time
from app.core.doris_client import get_doris_client

def monitor_doris_performance():
    client = get_doris_client()
    
    # 检查队列大小
    queue_size = client.log_queue.qsize()
    print(f"队列大小: {queue_size}")
    
    # 检查批量缓冲区
    buffer_size = len(client.batch_buffer)
    print(f"缓冲区大小: {buffer_size}")
    
    # 检查最后刷新时间
    last_flush = time.time() - client.last_flush_time
    print(f"上次刷新: {last_flush:.1f}秒前")
```

### 2. 日志监控

```bash
# 监控应用日志
tail -f logs/app.log | grep -i doris

# 监控错误日志
tail -f logs/app_error.log | grep -i doris
```

### 3. 数据库监控

```sql
-- 检查表大小
SELECT 
    table_name,
    table_rows,
    data_length,
    index_length
FROM information_schema.tables 
WHERE table_schema = 'acwl_logs';

-- 检查分区信息
SHOW PARTITIONS FROM api_access_logs;

-- 检查导入任务
SHOW LOAD;
```

## 故障排除

### 1. 连接问题

**问题**：无法连接到Doris

**解决方案**：
```bash
# 检查网络连通性
telnet your-doris-host 9030
telnet your-doris-host 8030

# 检查防火墙
sudo ufw status

# 检查Doris服务状态
sudo systemctl status doris-fe
sudo systemctl status doris-be
```

### 2. 写入失败

**问题**：数据写入失败

**解决方案**：
```python
# 检查错误日志
tail -f logs/app_error.log | grep "Stream Load"

# 手动测试写入
from app.core.doris_client import DorisClient
client = DorisClient()
client.log_access(
    method="GET",
    url="/test",
    status_code=200,
    response_time=0.1,
    client_ip="127.0.0.1"
)
```

### 3. 性能问题

**问题**：写入性能差

**解决方案**：
```python
# 调整批量参数
DORIS_BATCH_SIZE=1000
DORIS_FLUSH_INTERVAL=5

# 增加并发线程
# 在DorisClient中调整ThreadPoolExecutor的max_workers
```

### 4. 内存问题

**问题**：内存使用过高

**解决方案**：
```python
# 减少批量大小
DORIS_BATCH_SIZE=50

# 增加刷新频率
DORIS_FLUSH_INTERVAL=10

# 监控队列大小
queue_size = client.log_queue.qsize()
if queue_size > 1000:
    # 触发告警
    pass
```

### 5. 数据丢失

**问题**：部分数据丢失

**解决方案**：
```python
# 启用本地文件备份
# 访问日志会同时写入文件和Doris
# 可以从文件恢复丢失的数据

# 检查Doris导入历史
SHOW LOAD WHERE label LIKE '%api_access_logs%';
```

## 最佳实践

### 1. 配置建议

- **开发环境**：`DORIS_ENABLED=false`，使用文件日志
- **测试环境**：`DORIS_ENABLED=true`，小批量配置
- **生产环境**：`DORIS_ENABLED=true`，优化批量配置

### 2. 数据保留策略

```sql
-- 设置数据保留期
ALTER TABLE api_access_logs 
SET ("dynamic_partition.enable" = "true",
     "dynamic_partition.time_unit" = "DAY",
     "dynamic_partition.end" = "3",
     "dynamic_partition.prefix" = "p",
     "dynamic_partition.buckets" = "32",
     "dynamic_partition.history_partition_num" = "30");
```

### 3. 备份策略

```bash
# 定期备份重要数据
mysqldump -h doris-host -P 9030 -u root -p acwl_logs > backup.sql

# 或使用Doris的备份功能
BACKUP SNAPSHOT acwl_logs.snapshot_20240101
TO `s3://your-bucket/backup/`;
```

### 4. 安全建议

- 使用专用的Doris用户，限制权限
- 启用SSL连接（如果支持）
- 定期更新密码
- 监控异常访问

## 总结

通过集成Apache Doris，ACWL API系统获得了：

1. **高性能日志分析能力**：支持复杂的SQL查询和聚合分析
2. **实时数据洞察**：准实时的数据写入和查询
3. **成本优化**：高压缩比，降低存储成本
4. **扩展性**：支持PB级数据，满足业务增长需求
5. **易用性**：兼容MySQL协议，学习成本低

这种混合架构既保证了数据的可靠性（本地文件），又提供了强大的分析能力（Doris），是现代API系统日志管理的最佳实践。