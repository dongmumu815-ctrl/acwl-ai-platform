# 资源包设计文档

## 1. 概述

资源包是基于数据资源的查询条件预设方案，允许用户将某些查询条件设为固定值（锁定），其他条件作为动态查询参数。这样可以创建针对特定业务场景的数据查询模板。

## 2. 核心概念

### 2.1 资源包类型
- **SQL资源包**: 基于MySQL、Doris等关系型数据库的查询包
- **ES资源包**: 基于Elasticsearch的查询包

### 2.2 条件类型
- **锁定条件**: 固定不变的查询条件，如 `status = 1`
- **动态条件**: 可由用户在查询时指定的条件参数

### 2.3 资源包结构
```json
{
  "id": "资源包ID",
  "name": "资源包名称",
  "description": "资源包描述",
  "type": "sql|elasticsearch",
  "datasource_id": "数据源ID",
  "resource_id": "数据资源ID",
  "base_config": {
    "schema": "数据库/索引",
    "table": "表名/索引名",
    "fields": ["字段列表"]
  },
  "locked_conditions": [
    {
      "field": "字段名",
      "operator": "操作符",
      "value": "固定值",
      "logic": "AND|OR"
    }
  ],
  "dynamic_conditions": [
    {
      "field": "字段名",
      "operator": "操作符",
      "default_value": "默认值",
      "required": true,
      "description": "参数描述",
      "logic": "AND|OR"
    }
  ],
  "order_by": {
    "field": "排序字段",
    "direction": "ASC|DESC"
  },
  "limit": 1000,
  "created_by": "创建者ID",
  "created_at": "创建时间",
  "updated_at": "更新时间"
}
```

## 3. 数据库设计

### 3.1 资源包表 (resource_packages)
```sql
CREATE TABLE resource_packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL COMMENT '资源包名称',
    description TEXT COMMENT '资源包描述',
    type ENUM('sql', 'elasticsearch') NOT NULL COMMENT '资源包类型',
    datasource_id INT NOT NULL COMMENT '数据源ID',
    resource_id INT COMMENT '数据资源ID',
    base_config JSON COMMENT '基础配置',
    locked_conditions JSON COMMENT '锁定条件',
    dynamic_conditions JSON COMMENT '动态条件',
    order_config JSON COMMENT '排序配置',
    limit_config INT DEFAULT 1000 COMMENT '默认限制条数',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_datasource_id (datasource_id),
    INDEX idx_resource_id (resource_id),
    INDEX idx_created_by (created_by),
    INDEX idx_type (type)
);
```

### 3.2 资源包权限表 (resource_package_permissions)
```sql
CREATE TABLE resource_package_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    package_id INT NOT NULL COMMENT '资源包ID',
    user_id INT NOT NULL COMMENT '用户ID',
    permission_type ENUM('read', 'write', 'admin') NOT NULL COMMENT '权限类型',
    granted_by INT NOT NULL COMMENT '授权者ID',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    FOREIGN KEY (package_id) REFERENCES resource_packages(id) ON DELETE CASCADE,
    UNIQUE KEY uk_package_user (package_id, user_id)
);
```

## 4. API设计

### 4.1 资源包管理

#### 4.1.1 创建资源包
```
POST /api/v1/resource-packages
{
  "name": "活跃用户资源包",
  "description": "查询活跃状态的用户数据",
  "type": "sql",
  "datasource_id": 8,
  "resource_id": 123,
  "base_config": {
    "schema": "user_db",
    "table": "users",
    "fields": ["id", "name", "email", "status", "created_at"]
  },
  "locked_conditions": [
    {
      "field": "status",
      "operator": "=",
      "value": "1",
      "logic": "AND"
    }
  ],
  "dynamic_conditions": [
    {
      "field": "created_at",
      "operator": ">=",
      "default_value": "2024-01-01",
      "required": false,
      "description": "注册时间起始日期",
      "logic": "AND"
    }
  ]
}
```

#### 4.1.2 获取资源包列表
```
GET /api/v1/resource-packages?type=sql&datasource_id=8&page=1&size=20
```

#### 4.1.3 获取资源包详情
```
GET /api/v1/resource-packages/{package_id}
```

#### 4.1.4 更新资源包
```
PUT /api/v1/resource-packages/{package_id}
```

#### 4.1.5 删除资源包
```
DELETE /api/v1/resource-packages/{package_id}
```

### 4.2 资源包查询

#### 4.2.1 执行资源包查询
```
POST /api/v1/resource-packages/{package_id}/query
{
  "dynamic_params": {
    "created_at": "2024-06-01"
  },
  "limit": 500,
  "offset": 0
}
```

#### 4.2.2 获取资源包查询参数
```
GET /api/v1/resource-packages/{package_id}/params
```

## 5. 前端组件设计

### 5.1 资源包管理器 (ResourcePackageManager.vue)
- 资源包列表展示
- 创建/编辑资源包
- 权限管理

### 5.2 资源包构建器 (ResourcePackageBuilder.vue)
- 基于现有查询构建器扩展
- 条件锁定功能
- 动态参数配置

### 5.3 资源包查询器 (ResourcePackageQuery.vue)
- 动态参数输入
- 查询执行
- 结果展示

## 6. 使用场景示例

### 6.1 场景1: 活跃用户查询包
- **锁定条件**: `status = 1` (只查询活跃用户)
- **动态条件**: `created_at >= ?` (注册时间范围)
- **用途**: 运营团队查询不同时间段的活跃用户

### 6.2 场景2: 错误日志查询包
- **锁定条件**: `level = 'ERROR'` (只查询错误级别日志)
- **动态条件**: `timestamp >= ?` AND `service = ?` (时间和服务)
- **用途**: 开发团队快速查询特定服务的错误日志

### 6.3 场景3: 商品销售分析包
- **锁定条件**: `status = 'sold'` (已售出商品)
- **动态条件**: `category = ?` AND `price >= ?` (商品类别和价格范围)
- **用途**: 业务分析师分析不同类别商品的销售情况

## 7. 实现计划

### 阶段1: 后端API开发
1. 创建数据库表结构
2. 实现资源包CRUD API
3. 实现资源包查询API
4. 添加权限控制

### 阶段2: 前端组件开发
1. 资源包管理界面
2. 资源包构建器
3. 资源包查询界面
4. 集成到现有数据资源中心

### 阶段3: 功能增强
1. 资源包模板功能
2. 查询结果缓存
3. 查询历史记录
4. 资源包分享功能