# 分散前端项目独立部署指南

## 概述

本指南详细说明了如何独立部署三个前端项目，确保每个项目可以独立开发、构建和部署，同时保持整体系统的协调性。

## 项目部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx 反向代理                        │
│                     (端口: 80/443)                          │
└─────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │   主前端      │ │  工作流前端   │ │ 数据中心前端 │
        │ (端口: 3000) │ │ (端口: 3001) │ │ (端口: 3005) │
        │   /main/     │ │ /taskflow/  │ │   /data/    │
        └──────────────┘ └─────────────┘ └────────────┘
                                │
                        ┌───────▼──────┐
                        │   后端API     │
                        │ (端口: 8082)  │
                        │    /api/     │
                        └──────────────┘
```

## 开发环境配置

### 1. 端口分配
- **主前端**: `http://localhost:3000`
- **工作流前端**: `http://localhost:3001`
- **数据中心前端**: `http://localhost:3005`
- **后端API**: `http://localhost:8082`

### 2. 启动脚本

创建统一的启动脚本 `start-all-dev.bat`:

```batch
@echo off
echo 启动所有前端开发服务器...

echo 启动主前端 (端口: 3000)...
start "主前端" cmd /k "cd /d d:\works\codes\acwl-ai-data\frontend && npm run dev"

echo 启动工作流前端 (端口: 3001)...
start "工作流前端" cmd /k "cd /d d:\works\codes\acwl-ai-data\taskflow-frontend && npm run dev"

echo 启动数据中心前端 (端口: 3005)...
start "数据中心前端" cmd /k "cd /d d:\works\codes\acwl-ai-data\dc_frontend && npm run dev"

echo 所有前端服务器启动完成！
echo 主前端: http://localhost:3000
echo 工作流前端: http://localhost:3001
echo 数据中心前端: http://localhost:3005
pause
```

### 3. 环境变量配置

为每个项目创建 `.env` 文件：

**frontend/.env**:
```env
# 主前端环境变量
VITE_APP_TITLE=ACWL AI大模型管理平台
VITE_API_BASE_URL=http://localhost:8082/api
VITE_APP_PORT=3000
VITE_APP_BASE_PATH=/main/
```

**taskflow-frontend/.env**:
```env
# 工作流前端环境变量
VITE_APP_TITLE=ACWL AI工作流管理平台
VITE_API_BASE_URL=http://localhost:8082/api
VITE_APP_PORT=3001
VITE_APP_BASE_PATH=/taskflow/
```

**dc_frontend/.env**:
```env
# 数据中心前端环境变量
VITE_APP_TITLE=数据资源中心
VITE_API_BASE_URL=http://localhost:8082/api
VITE_APP_PORT=3005
VITE_APP_BASE_PATH=/data/
```

## 生产环境部署

### 1. 构建配置优化

**统一的构建脚本 `build-all.bat`**:
```batch
@echo off
echo 开始构建所有前端项目...

echo 构建主前端...
cd /d d:\works\codes\acwl-ai-data\frontend
call npm run build
if %errorlevel% neq 0 (
    echo 主前端构建失败！
    pause
    exit /b 1
)

echo 构建工作流前端...
cd /d d:\works\codes\acwl-ai-data\taskflow-frontend
call npm run build
if %errorlevel% neq 0 (
    echo 工作流前端构建失败！
    pause
    exit /b 1
)

echo 构建数据中心前端...
cd /d d:\works\codes\acwl-ai-data\dc_frontend
call npm run build
if %errorlevel% neq 0 (
    echo 数据中心前端构建失败！
    pause
    exit /b 1
)

echo 所有前端项目构建完成！
pause
```

### 2. Nginx 配置

**nginx.conf**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 主前端
    location /main/ {
        alias /var/www/frontend/dist/;
        try_files $uri $uri/ /main/index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 工作流前端
    location /taskflow/ {
        alias /var/www/taskflow-frontend/dist/;
        try_files $uri $uri/ /taskflow/index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 数据中心前端
    location /data/ {
        alias /var/www/dc_frontend/dist/;
        try_files $uri $uri/ /data/index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API代理
    location /api/ {
        proxy_pass http://localhost:8082/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 默认重定向到主前端
    location = / {
        return 301 /main/;
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 3. Docker 部署配置

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # 主前端
  frontend-main:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: acwl-frontend-main
    ports:
      - "3000:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
    restart: unless-stopped

  # 工作流前端
  frontend-taskflow:
    build:
      context: ./taskflow-frontend
      dockerfile: Dockerfile
    container_name: acwl-frontend-taskflow
    ports:
      - "3001:80"
    volumes:
      - ./taskflow-frontend/dist:/usr/share/nginx/html
    restart: unless-stopped

  # 数据中心前端
  frontend-data:
    build:
      context: ./dc_frontend
      dockerfile: Dockerfile
    container_name: acwl-frontend-data
    ports:
      - "3005:80"
    volumes:
      - ./dc_frontend/dist:/usr/share/nginx/html
    restart: unless-stopped

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: acwl-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend-main
      - frontend-taskflow
      - frontend-data
    restart: unless-stopped
```

**Dockerfile (通用)**:
```dockerfile
# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine as production-stage

# 复制构建结果
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## 持续集成/持续部署 (CI/CD)

### 1. GitHub Actions 配置

**.github/workflows/deploy.yml**:
```yaml
name: Deploy Frontend Applications

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        app: [frontend, taskflow-frontend, dc_frontend]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: ${{ matrix.app }}/package-lock.json
    
    - name: Install dependencies
      run: |
        cd ${{ matrix.app }}
        npm ci
    
    - name: Run tests
      run: |
        cd ${{ matrix.app }}
        npm run test:unit
    
    - name: Build application
      run: |
        cd ${{ matrix.app }}
        npm run build
    
    - name: Deploy to server
      if: github.ref == 'refs/heads/main'
      run: |
        # 部署脚本
        echo "Deploying ${{ matrix.app }} to production server"
```

### 2. 部署脚本

**deploy.sh**:
```bash
#!/bin/bash

# 分散前端项目部署脚本

set -e

echo "开始部署前端项目..."

# 定义项目路径
PROJECTS=("frontend" "taskflow-frontend" "dc_frontend")
DEPLOY_PATH="/var/www"

# 备份当前版本
backup_current() {
    local project=$1
    if [ -d "$DEPLOY_PATH/$project" ]; then
        echo "备份 $project..."
        mv "$DEPLOY_PATH/$project" "$DEPLOY_PATH/${project}_backup_$(date +%Y%m%d_%H%M%S)"
    fi
}

# 部署新版本
deploy_project() {
    local project=$1
    echo "部署 $project..."
    
    # 构建项目
    cd "$project"
    npm ci
    npm run build
    
    # 备份当前版本
    backup_current "$project"
    
    # 部署新版本
    mkdir -p "$DEPLOY_PATH/$project"
    cp -r dist/* "$DEPLOY_PATH/$project/"
    
    echo "$project 部署完成"
    cd ..
}

# 部署所有项目
for project in "${PROJECTS[@]}"; do
    deploy_project "$project"
done

# 重启Nginx
echo "重启Nginx..."
sudo systemctl reload nginx

echo "所有前端项目部署完成！"
```

## 监控和维护

### 1. 健康检查

**health-check.sh**:
```bash
#!/bin/bash

# 前端项目健康检查脚本

ENDPOINTS=(
    "http://localhost:3000/main/"
    "http://localhost:3001/taskflow/"
    "http://localhost:3005/data/"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo "检查 $endpoint..."
    
    if curl -f -s "$endpoint" > /dev/null; then
        echo "✅ $endpoint 正常"
    else
        echo "❌ $endpoint 异常"
        # 发送告警通知
        # send_alert "$endpoint is down"
    fi
done
```

### 2. 日志管理

**nginx日志配置**:
```nginx
# 为每个前端项目配置独立的日志
log_format frontend_log '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       '$request_time $upstream_response_time';

server {
    # 主前端日志
    location /main/ {
        access_log /var/log/nginx/frontend_main_access.log frontend_log;
        error_log /var/log/nginx/frontend_main_error.log;
    }
    
    # 工作流前端日志
    location /taskflow/ {
        access_log /var/log/nginx/frontend_taskflow_access.log frontend_log;
        error_log /var/log/nginx/frontend_taskflow_error.log;
    }
    
    # 数据中心前端日志
    location /data/ {
        access_log /var/log/nginx/frontend_data_access.log frontend_log;
        error_log /var/log/nginx/frontend_data_error.log;
    }
}
```

## 性能优化

### 1. 缓存策略
- 静态资源长期缓存 (1年)
- HTML文件不缓存
- API响应适当缓存

### 2. 压缩配置
```nginx
# Gzip压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/javascript
    application/xml+rss
    application/json;
```

### 3. CDN配置
- 静态资源使用CDN加速
- 图片资源优化和压缩
- 字体文件本地化

## 故障排除

### 1. 常见问题
- **端口冲突**: 检查端口占用情况
- **构建失败**: 检查依赖版本和Node.js版本
- **代理错误**: 检查API服务器状态和代理配置

### 2. 回滚策略
```bash
# 快速回滚脚本
rollback_project() {
    local project=$1
    local backup_dir=$(ls -t "$DEPLOY_PATH/${project}_backup_"* | head -1)
    
    if [ -n "$backup_dir" ]; then
        echo "回滚 $project 到 $backup_dir..."
        rm -rf "$DEPLOY_PATH/$project"
        mv "$backup_dir" "$DEPLOY_PATH/$project"
        echo "$project 回滚完成"
    else
        echo "未找到 $project 的备份版本"
    fi
}
```

## 总结

通过这套完整的独立部署方案，我们可以：

1. **独立开发**: 每个前端项目可以独立开发和测试
2. **独立部署**: 支持单独部署某个前端项目
3. **统一管理**: 通过Nginx统一入口和路由
4. **性能优化**: 缓存、压缩、CDN等优化策略
5. **监控维护**: 健康检查、日志管理、故障排除

这种分散的架构既保持了项目的独立性，又确保了整体系统的协调性和可维护性。