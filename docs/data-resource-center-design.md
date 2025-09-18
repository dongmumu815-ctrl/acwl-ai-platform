# 数据资源中心设计方案

## 1. 项目概述

### 1.1 背景
在数据加工过程中，通过ODS、DWD、DWS等层级处理后，需要将部分表放入数据资源中心，供授权用户查看和使用。数据资源中心支持两种数据源：
- Doris加工库表
- Elasticsearch索引

### 1.2 目标
- 统一管理数据资源
- 提供细粒度的权限控制
- 支持多种数据源类型
- 与现有数据中台风格保持一致

## 2. 系统架构设计

### 2.1 整体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   dc_frontend   │    │     backend     │    │   数据源层      │
│  数据资源中心    │◄──►│   API服务层     │◄──►│  Doris/ES      │
│     前端        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   MySQL数据库   │
                       │   元数据存储    │
                       └─────────────────┘
```

### 2.2 技术栈
- **前端**: Vue 3 + TypeScript + Element Plus + Vite
- **后端**: FastAPI + SQLAlchemy + MySQL
- **数据源**: Doris + Elasticsearch
- **认证**: 复用现有用户认证系统

## 3. 数据库设计

### 3.1 数据资源表 (acwl_data_resources)
```sql
CREATE TABLE acwl_data_resources (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '资源ID',
    name VARCHAR(100) NOT NULL COMMENT '资源名称',
    display_name VARCHAR(100) NOT NULL COMMENT '显示名称',
    description TEXT COMMENT '资源描述',
    resource_type ENUM('doris_table', 'elasticsearch_index') NOT NULL COMMENT '资源类型',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    database_name VARCHAR(100) COMMENT '数据库名称(Doris)',
    table_name VARCHAR(100) COMMENT '表名称(Doris)',
    index_name VARCHAR(100) COMMENT '索引名称(ES)',
    schema_info JSON COMMENT '表结构信息',
    tags JSON COMMENT '标签信息',
    category VARCHAR(50) COMMENT '分类',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    status ENUM('active', 'inactive', 'archived') DEFAULT 'active' COMMENT '状态',
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (datasource_id) REFERENCES acwl_datasources(id),
    FOREIGN KEY (created_by) REFERENCES acwl_users(id),
    INDEX idx_resource_type (resource_type),
    INDEX idx_category (category),
    INDEX idx_status (status)
) COMMENT '数据资源表';
```

### 3.2 资源权限表 (acwl_data_resource_permissions)
```sql
CREATE TABLE acwl_data_resource_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    user_id INT COMMENT '用户ID',
    role_id INT COMMENT '角色ID',
    permission_type ENUM('read', 'write', 'admin') NOT NULL COMMENT '权限类型',
    granted_by INT NOT NULL COMMENT '授权者ID',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES acwl_users(id),
    FOREIGN KEY (granted_by) REFERENCES acwl_users(id),
    UNIQUE KEY uk_resource_user (resource_id, user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_permission_type (permission_type)
) COMMENT '数据资源权限表';
```

### 3.3 资源分类表 (acwl_data_resource_categories)
```sql
CREATE TABLE acwl_data_resource_categories (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '分类ID',
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    display_name VARCHAR(50) NOT NULL COMMENT '显示名称',
    description TEXT COMMENT '分类描述',
    parent_id INT COMMENT '父分类ID',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (parent_id) REFERENCES acwl_data_resource_categories(id),
    UNIQUE KEY uk_name (name),
    INDEX idx_parent_id (parent_id)
) COMMENT '数据资源分类表';
```

### 3.4 资源访问日志表 (acwl_data_resource_access_logs)
```sql
CREATE TABLE acwl_data_resource_access_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    resource_id INT NOT NULL COMMENT '资源ID',
    user_id INT NOT NULL COMMENT '用户ID',
    access_type ENUM('view', 'query', 'download', 'preview') NOT NULL COMMENT '访问类型',
    query_sql TEXT COMMENT '查询SQL',
    result_count INT COMMENT '结果数量',
    execution_time INT COMMENT '执行时间(毫秒)',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    status ENUM('success', 'failed', 'timeout') NOT NULL COMMENT '状态',
    error_message TEXT COMMENT '错误信息',
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '访问时间',
    FOREIGN KEY (resource_id) REFERENCES acwl_data_resources(id),
    FOREIGN KEY (user_id) REFERENCES acwl_users(id),
    INDEX idx_resource_user (resource_id, user_id),
    INDEX idx_accessed_at (accessed_at)
) COMMENT '数据资源访问日志表';
```

## 4. API接口设计

### 4.1 资源管理接口

#### 4.1.1 获取资源列表
```
GET /api/v1/data-resources
参数:
- page: 页码
- size: 每页大小
- category: 分类筛选
- resource_type: 资源类型筛选
- keyword: 关键词搜索
- tags: 标签筛选
```

#### 4.1.2 获取资源详情
```
GET /api/v1/data-resources/{resource_id}
```

#### 4.1.3 创建资源
```
POST /api/v1/data-resources
请求体:
{
  "name": "string",
  "display_name": "string",
  "description": "string",
  "resource_type": "doris_table|elasticsearch_index",
  "datasource_id": "integer",
  "database_name": "string",
  "table_name": "string",
  "index_name": "string",
  "category": "string",
  "tags": ["string"],
  "is_public": "boolean"
}
```

#### 4.1.4 更新资源
```
PUT /api/v1/data-resources/{resource_id}
```

#### 4.1.5 删除资源
```
DELETE /api/v1/data-resources/{resource_id}
```

### 4.2 权限管理接口

#### 4.2.1 获取资源权限
```
GET /api/v1/data-resources/{resource_id}/permissions
```

#### 4.2.2 授权用户
```
POST /api/v1/data-resources/{resource_id}/permissions
请求体:
{
  "user_id": "integer",
  "permission_type": "read|write|admin",
  "expires_at": "datetime"
}
```

#### 4.2.3 撤销权限
```
DELETE /api/v1/data-resources/{resource_id}/permissions/{permission_id}
```

### 4.3 数据查询接口

#### 4.3.1 预览数据
```
GET /api/v1/data-resources/{resource_id}/preview
参数:
- limit: 限制行数(默认100)
```

#### 4.3.2 查询数据
```
POST /api/v1/data-resources/{resource_id}/query
请求体:
{
  "query": "string",  // SQL查询语句或ES查询DSL
  "limit": "integer",
  "offset": "integer"
}
```

#### 4.3.3 获取表结构
```
GET /api/v1/data-resources/{resource_id}/schema
```

### 4.4 分类管理接口

#### 4.4.1 获取分类树
```
GET /api/v1/data-resource-categories
```

#### 4.4.2 创建分类
```
POST /api/v1/data-resource-categories
```

## 5. 前端设计

### 5.1 页面结构
```
dc_frontend/
├── src/
│   ├── views/
│   │   ├── dashboard/           # 数据资源仪表盘
│   │   ├── resources/           # 资源管理
│   │   │   ├── list.vue        # 资源列表
│   │   │   ├── detail.vue      # 资源详情
│   │   │   ├── create.vue      # 创建资源
│   │   │   └── query.vue       # 数据查询
│   │   ├── permissions/         # 权限管理
│   │   ├── categories/          # 分类管理
│   │   └── logs/               # 访问日志
│   ├── components/
│   │   ├── ResourceCard.vue     # 资源卡片
│   │   ├── QueryEditor.vue      # 查询编辑器
│   │   ├── SchemaViewer.vue     # 表结构查看器
│   │   ├── PermissionManager.vue # 权限管理器
│   │   └── CategoryTree.vue     # 分类树
│   ├── api/
│   │   ├── resources.ts         # 资源API
│   │   ├── permissions.ts       # 权限API
│   │   └── categories.ts        # 分类API
│   └── types/
│       ├── resource.ts          # 资源类型定义
│       └── permission.ts        # 权限类型定义
```

### 5.2 主要组件设计

#### 5.2.1 资源列表页面
- 支持分类筛选
- 支持关键词搜索
- 支持标签筛选
- 卡片式展示资源
- 分页加载

#### 5.2.2 资源详情页面
- 基本信息展示
- 表结构查看
- 数据预览
- 权限管理
- 访问统计

#### 5.2.3 数据查询页面
- SQL编辑器(Monaco Editor)
- 查询结果表格
- 导出功能
- 查询历史

### 5.3 样式规范
复用现有frontend项目的样式变量和组件库：
- 使用Element Plus组件库
- 复用variables.scss中的颜色变量
- 保持与主系统一致的布局和交互

## 6. 权限控制设计

### 6.1 权限级别
- **read**: 只读权限，可查看资源信息和预览数据
- **write**: 读写权限，可执行查询和导出数据
- **admin**: 管理权限，可管理资源和分配权限

### 6.2 权限继承
- 系统管理员拥有所有资源的admin权限
- 资源创建者默认拥有admin权限
- 公开资源所有用户拥有read权限

### 6.3 权限检查
- API层面进行权限验证
- 前端根据权限控制功能显示
- 数据查询时验证用户权限

## 7. 安全考虑

### 7.1 SQL注入防护
- 使用参数化查询
- SQL语句白名单检查
- 查询复杂度限制

### 7.2 数据脱敏
- 敏感字段自动脱敏
- 可配置脱敏规则
- 预览数据限制

### 7.3 访问控制
- 基于角色的访问控制(RBAC)
- 细粒度权限管理
- 访问日志记录

## 8. 性能优化

### 8.1 查询优化
- 查询结果缓存
- 分页查询
- 查询超时控制

### 8.2 前端优化
- 虚拟滚动
- 懒加载
- 组件缓存

## 9. 监控和日志

### 9.1 访问监控
- 用户访问统计
- 资源使用情况
- 查询性能监控

### 9.2 日志记录
- 用户操作日志
- 系统错误日志
- 安全审计日志

## 10. 部署方案

### 10.1 开发环境
- dc_frontend独立开发服务器
- 复用backend API服务
- 本地数据库开发

### 10.2 生产环境
- 前端静态资源部署
- API服务集成到现有backend
- 数据库迁移脚本

## 11. 开发计划

### 阶段一：基础功能(2周)
- 数据库表设计和创建
- 基础API接口开发
- 前端项目搭建
- 资源列表和详情页面

### 阶段二：核心功能(2周)
- 权限管理系统
- 数据查询功能
- 分类管理
- 基础安全控制

### 阶段三：高级功能(1周)
- 访问日志和统计
- 性能优化
- 监控和告警
- 测试和部署

## 12. 风险评估

### 12.1 技术风险
- 数据源连接稳定性
- 查询性能问题
- 权限控制复杂性

### 12.2 安全风险
- 数据泄露风险
- 权限提升攻击
- SQL注入攻击

### 12.3 缓解措施
- 完善的测试覆盖
- 安全代码审查
- 监控和告警机制