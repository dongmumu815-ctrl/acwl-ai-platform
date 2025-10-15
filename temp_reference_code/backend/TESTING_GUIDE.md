# API性能测试指南

## 概述

本指南提供了两种性能测试方案，帮助您验证API优化效果：

1. **简化版测试** - 仅使用Python标准库，无需额外依赖
2. **完整版测试** - 使用aiohttp进行异步测试，功能更强大

## 快速开始（推荐）

### 方案1: 简化版测试

**优点**: 无需安装额外依赖，开箱即用  
**适用场景**: 快速验证API性能，基础测试需求

```bash
# 直接运行，无需安装依赖
python simple_performance_test.py
```

### 方案2: 完整版测试

**优点**: 支持真正的异步并发，测试结果更准确  
**适用场景**: 生产环境性能测试，详细性能分析

```bash
# 安装测试依赖
pip install aiohttp

# 或安装完整测试套件
pip install -r test_requirements.txt

# 运行完整测试
python performance_test.py
```

## 详细配置

### 1. 修改测试配置

在运行测试前，请根据您的环境修改以下配置：

#### simple_performance_test.py 配置
```python
# 测试配置
BASE_URL = "http://localhost:8000/api/v1"  # 修改为您的API地址
API_CODE = "test_api"                      # 修改为实际的API代码
TEST_COUNT = 20                            # 测试次数
CONCURRENT_REQUESTS = 5                    # 并发请求数
TIMEOUT = 10                               # 请求超时时间（秒）

# 测试数据
TEST_DATA = {
    "field1": "test_value",
    "field2": 123,
    "batch_id": "test_batch"
}

# 如果API需要认证，请取消注释并填入token
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Performance-Test-Script/1.0",
    # "Authorization": "Bearer your_token_here"
}
```

#### performance_test.py 配置
```python
# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
API_CODE = "test_api"                      # 替换为实际的API代码
TEST_COUNT = 50                            # 测试次数
CONCURRENT_REQUESTS = 10                   # 并发请求数

# 认证头（如果需要）
HEADERS = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer your_token_here"
}
```

### 2. 获取API代码和认证信息

#### 查找可用的API代码
```bash
# 查看数据库中的API配置
python check_api_config.py

# 或者查看API列表
curl http://localhost:8000/api/v1/admin/apis
```

#### 获取认证Token（如果需要）
```bash
# 登录获取token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

## 运行测试

### 启动API服务

确保API服务正在运行：

```bash
# 进入backend目录
cd d:\works\codes\acwl-api\backend

# 启动API服务
python main.py

# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 运行性能测试

#### 简化版测试
```bash
# Windows
python simple_performance_test.py

# 或使用完整路径
python d:\works\codes\acwl-api\backend\simple_performance_test.py
```

#### 完整版测试
```bash
# 先安装依赖
pip install aiohttp

# 运行测试
python performance_test.py
```

## 测试结果解读

### 关键指标

1. **平均响应时间**: 所有成功请求的平均耗时
2. **95%百分位**: 95%的请求在此时间内完成
3. **99%百分位**: 99%的请求在此时间内完成
4. **成功率**: 成功请求占总请求的比例

### 性能评估标准

- **优秀**: 平均响应时间 < 100ms
- **良好**: 平均响应时间 < 200ms
- **一般**: 平均响应时间 < 500ms
- **需要优化**: 平均响应时间 >= 500ms

### 示例输出

```
📊 性能测试结果分析
==================================================
📈 请求统计:
   - 总请求数: 20
   - 成功请求: 20
   - 失败请求: 0
   - 成功率: 100.00%

⏱️  响应时间统计:
   - 平均响应时间: 156.23ms
   - 中位数响应时间: 145.67ms
   - 最小响应时间: 98.45ms
   - 最大响应时间: 234.56ms
   - 95%百分位: 198.34ms
   - 99%百分位: 234.56ms

🎯 性能评估:
   ✅ 良好 - 平均响应时间 < 200ms
   - 平均响应大小: 156 bytes

📊 响应时间分布:
   - 快速响应 (<100ms): 1 次 (5.0%)
   - 中等响应 (100-300ms): 19 次 (95.0%)
   - 慢速响应 (>=300ms): 0 次 (0.0%)
```

## 故障排除

### 常见问题

#### 1. ModuleNotFoundError: No module named 'aiohttp'

**解决方案**:
```bash
# 安装aiohttp
pip install aiohttp

# 或使用简化版测试
python simple_performance_test.py
```

#### 2. 连接被拒绝 (Connection refused)

**可能原因**:
- API服务未启动
- 端口号错误
- 防火墙阻止连接

**解决方案**:
```bash
# 检查API服务状态
netstat -an | findstr :8000

# 启动API服务
python main.py

# 检查服务健康状态
curl http://localhost:8000/docs
```

#### 3. HTTP 404 Not Found

**可能原因**:
- API_CODE不存在
- URL路径错误

**解决方案**:
```bash
# 查看可用的API
python check_api_config.py

# 或查看数据库
sqlite3 app.db "SELECT api_code, status FROM custom_apis;"
```

#### 4. HTTP 401 Unauthorized

**可能原因**:
- API需要认证但未提供token
- Token已过期或无效

**解决方案**:
```python
# 在测试脚本中添加认证头
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_valid_token_here"
}
```

#### 5. 响应时间异常高

**可能原因**:
- 数据库连接问题
- 服务器资源不足
- 网络延迟

**解决方案**:
1. 检查数据库连接
2. 监控服务器资源使用
3. 查看API服务日志
4. 参考 `PERFORMANCE_OPTIMIZATION.md` 进行优化

### 调试技巧

#### 1. 启用详细日志
```python
# 在API服务中启用DEBUG日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 单次请求测试
```bash
# 使用curl测试单个请求
curl -X POST http://localhost:8000/api/v1/your_api_code \
  -H "Content-Type: application/json" \
  -d '{"field1":"test_value","field2":123}' \
  -w "\nTime: %{time_total}s\n"
```

#### 3. 监控系统资源
```bash
# Windows任务管理器
taskmgr

# 或使用PowerShell
Get-Process python
Get-Counter "\Processor(_Total)\% Processor Time"
```

## 性能基准

### 优化前后对比

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 平均响应时间 | 600-700ms | 200-300ms | 50-60% |
| 95%百分位 | 800-900ms | 300-400ms | 55-60% |
| 成功率 | 95-98% | 99%+ | 1-4% |

### 目标性能指标

- **生产环境目标**:
  - 平均响应时间: < 200ms
  - 95%百分位: < 300ms
  - 99%百分位: < 500ms
  - 成功率: > 99.9%

- **开发环境目标**:
  - 平均响应时间: < 300ms
  - 95%百分位: < 500ms
  - 成功率: > 99%

## 进阶测试

### 1. 压力测试

增加并发数和测试次数：

```python
# 高并发测试配置
TEST_COUNT = 100
CONCURRENT_REQUESTS = 20
```

### 2. 长时间测试

```python
# 持续测试30分钟
import time

start_time = time.time()
test_duration = 30 * 60  # 30分钟

while time.time() - start_time < test_duration:
    run_performance_test()
    time.sleep(60)  # 每分钟测试一次
```

### 3. 不同场景测试

```python
# 测试不同的API端点
api_endpoints = ["api1", "api2", "api3"]

for api_code in api_endpoints:
    print(f"\n测试API: {api_code}")
    # 运行测试
```

## 总结

通过本指南，您可以：

1. ✅ 快速验证API性能优化效果
2. ✅ 识别性能瓶颈
3. ✅ 监控系统稳定性
4. ✅ 为进一步优化提供数据支持

建议定期运行性能测试，特别是在代码变更后，以确保性能不会退化。