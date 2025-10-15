# 生产环境启动指南

本文档介绍如何在生产环境中启动CEPIEC API服务器。

## 📋 前置要求

1. **Python 3.8+** 已安装
2. **依赖包** 已安装：`pip install -r requirements.txt`
3. **环境配置** 已完成：复制`.env.example`为`.env`并配置相应参数
4. **数据库** 已初始化并可连接

## 🚀 启动方式

### 方式一：使用批处理脚本（推荐 - Windows）

```bash
# 双击运行或在命令行执行
start_production.bat
```

**特点：**
- ✅ 自动检查Python环境
- ✅ 自动激活虚拟环境（如果存在）
- ✅ 自动安装缺失依赖
- ✅ 友好的中文提示
- ✅ 适合Windows环境

### 方式二：使用Python启动脚本

```bash
# 生产模式启动（默认8080端口）
python start_server.py

# 指定端口启动
python start_server.py --port 9000

# 指定工作进程数
python start_server.py --workers 8

# 开发模式启动（使用Uvicorn）
python start_server.py --dev

# 开发模式 + 自动重载
python start_server.py --dev --reload
```

### 方式三：直接使用Gunicorn

```bash
# 使用配置文件启动
gunicorn --config gunicorn.conf.py main:app

# 手动指定参数启动
gunicorn --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn.workers.UvicornWorker main:app
```

### 方式四：使用原始启动脚本

```bash
# 功能完整的生产启动脚本
python start_production.py
```

## ⚙️ 配置说明

### Gunicorn配置文件 (`gunicorn.conf.py`)

主要配置项：

```python
# 服务绑定
bind = "0.0.0.0:8080"  # 监听地址和端口

# 工作进程
workers = CPU核心数 * 2 + 1  # 工作进程数
worker_class = "uvicorn.workers.UvicornWorker"  # Worker类型
worker_connections = 1000  # 每个worker的连接数

# 性能优化
max_requests = 1000  # 每个worker处理请求数后重启
preload_app = True  # 预加载应用
timeout = 30  # 请求超时时间
```

### 环境变量配置

根据不同环境设置：

```bash
# 开发环境
export ENVIRONMENT=development

# 生产环境
export ENVIRONMENT=production
```

## 🔧 性能调优

### 工作进程数建议

- **CPU密集型应用**：`workers = CPU核心数`
- **I/O密集型应用**：`workers = CPU核心数 * 2 + 1`
- **混合型应用**：`workers = CPU核心数 * 1.5`

### 内存使用优化

```python
# 启用预加载减少内存使用
preload_app = True

# 设置worker重启阈值
max_requests = 1000
max_requests_jitter = 50
```

### 连接数调优

```python
# 根据服务器配置调整
worker_connections = 1000  # 单个worker最大连接数
backlog = 2048  # 等待队列大小
```

## 📊 监控和日志

### 访问日志

```bash
# 实时查看访问日志
tail -f /var/log/gunicorn/access.log
```

### 错误日志

```bash
# 实时查看错误日志
tail -f /var/log/gunicorn/error.log
```

### 进程监控

```bash
# 查看Gunicorn进程
ps aux | grep gunicorn

# 查看端口占用
netstat -tlnp | grep 8080
```

## 🛡️ 安全建议

### 1. 运行用户

```python
# 在gunicorn.conf.py中设置
user = "www-data"  # 非root用户
group = "www-data"
```

### 2. 防火墙配置

```bash
# 只允许必要端口
sudo ufw allow 8080/tcp
sudo ufw enable
```

### 3. 反向代理

建议在生产环境中使用Nginx作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔄 进程管理

### 使用systemd（Linux）

创建服务文件 `/etc/systemd/system/cepiec-api.service`：

```ini
[Unit]
Description=CEPIEC API Server
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python start_production.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable cepiec-api
sudo systemctl start cepiec-api
sudo systemctl status cepiec-api
```

### 使用PM2（跨平台）

```bash
# 安装PM2
npm install -g pm2

# 启动应用
pm2 start start_production.py --name cepiec-api

# 查看状态
pm2 status

# 查看日志
pm2 logs cepiec-api
```

## 🚨 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查找占用进程
   lsof -i :8080
   # 杀死进程
   kill -9 <PID>
   ```

2. **依赖包缺失**
   ```bash
   pip install -r requirements.txt
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   ls -la
   # 修改权限
   chmod +x start_production.py
   ```

4. **数据库连接失败**
   - 检查`.env`文件中的数据库配置
   - 确认数据库服务正在运行
   - 验证网络连接

### 日志分析

```bash
# 查看最近的错误
grep -i error /var/log/gunicorn/error.log | tail -20

# 查看访问统计
awk '{print $1}' /var/log/gunicorn/access.log | sort | uniq -c | sort -nr
```

## 📈 性能测试

### 使用Apache Bench

```bash
# 并发测试
ab -n 1000 -c 10 http://localhost:8080/health
```

### 使用wrk

```bash
# 压力测试
wrk -t12 -c400 -d30s http://localhost:8080/health
```

## 📞 技术支持

如果遇到问题，请检查：

1. 📋 **日志文件** - 查看详细错误信息
2. 🔧 **配置文件** - 确认所有配置正确
3. 🌐 **网络连接** - 验证端口和防火墙设置
4. 💾 **系统资源** - 检查CPU、内存、磁盘使用情况

---

**祝您部署顺利！** 🎉