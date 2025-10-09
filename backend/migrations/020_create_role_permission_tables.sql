-- 创建角色权限系统表
-- 迁移文件: 020_create_role_permission_tables.sql

-- 1. 创建角色表
CREATE TABLE IF NOT EXISTS `acwl_roles` (
    `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '角色ID',
    `name` varchar(50) NOT NULL COMMENT '角色名称',
    `code` varchar(50) NOT NULL COMMENT '角色代码',
    `description` text COMMENT '角色描述',
    `is_system` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为系统角色（系统角色不可删除）',
    `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `created_by` int(11) DEFAULT NULL COMMENT '创建者ID',
    `updated_by` int(11) DEFAULT NULL COMMENT '更新者ID',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_code` (`code`),
    UNIQUE KEY `uk_role_name` (`name`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- 2. 创建权限表
CREATE TABLE IF NOT EXISTS `acwl_permissions` (
    `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '权限ID',
    `name` varchar(100) NOT NULL COMMENT '权限名称',
    `code` varchar(100) NOT NULL COMMENT '权限代码',
    `description` text COMMENT '权限描述',
    `module` varchar(50) NOT NULL COMMENT '所属模块',
    `resource` varchar(100) DEFAULT NULL COMMENT '资源标识',
    `action` varchar(50) NOT NULL COMMENT '操作类型（create/read/update/delete/execute等）',
    `is_system` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为系统权限（系统权限不可删除）',
    `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    `sort_order` int(11) DEFAULT 0 COMMENT '排序顺序',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `created_by` int(11) DEFAULT NULL COMMENT '创建者ID',
    `updated_by` int(11) DEFAULT NULL COMMENT '更新者ID',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_permission_code` (`code`),
    KEY `idx_module` (`module`),
    KEY `idx_resource` (`resource`),
    KEY `idx_action` (`action`),
    KEY `idx_status` (`status`),
    KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

-- 3. 创建用户角色关联表
CREATE TABLE IF NOT EXISTS `acwl_user_roles` (
    `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    `user_id` int(11) NOT NULL COMMENT '用户ID',
    `role_id` int(11) NOT NULL COMMENT '角色ID',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `created_by` int(11) DEFAULT NULL COMMENT '创建者ID',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_role` (`user_id`, `role_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_role_id` (`role_id`),
    CONSTRAINT `fk_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `acwl_users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_roles_role` FOREIGN KEY (`role_id`) REFERENCES `acwl_roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- 4. 创建角色权限关联表
CREATE TABLE IF NOT EXISTS `acwl_role_permissions` (
    `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    `role_id` int(11) NOT NULL COMMENT '角色ID',
    `permission_id` int(11) NOT NULL COMMENT '权限ID',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `created_by` int(11) DEFAULT NULL COMMENT '创建者ID',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_permission` (`role_id`, `permission_id`),
    KEY `idx_role_id` (`role_id`),
    KEY `idx_permission_id` (`permission_id`),
    CONSTRAINT `fk_role_permissions_role` FOREIGN KEY (`role_id`) REFERENCES `acwl_roles` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_role_permissions_permission` FOREIGN KEY (`permission_id`) REFERENCES `acwl_permissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- 插入默认系统角色
INSERT INTO `acwl_roles` (`name`, `code`, `description`, `is_system`, `status`) VALUES
('超级管理员', 'super_admin', '系统超级管理员，拥有所有权限', 1, 1),
('管理员', 'admin', '系统管理员，拥有大部分管理权限', 1, 1),
('普通用户', 'user', '普通用户，拥有基本使用权限', 1, 1),
('访客', 'guest', '访客用户，只有查看权限', 1, 1);

-- 插入默认系统权限
INSERT INTO `acwl_permissions` (`name`, `code`, `description`, `module`, `resource`, `action`, `is_system`, `status`, `sort_order`) VALUES
-- 系统管理权限
('用户管理-查看', 'system.user.read', '查看用户列表和详情', '系统管理', 'user', 'read', 1, 1, 100),
('用户管理-创建', 'system.user.create', '创建新用户', '系统管理', 'user', 'create', 1, 1, 101),
('用户管理-编辑', 'system.user.update', '编辑用户信息', '系统管理', 'user', 'update', 1, 1, 102),
('用户管理-删除', 'system.user.delete', '删除用户', '系统管理', 'user', 'delete', 1, 1, 103),
('角色管理-查看', 'system.role.read', '查看角色列表和详情', '系统管理', 'role', 'read', 1, 1, 110),
('角色管理-创建', 'system.role.create', '创建新角色', '系统管理', 'role', 'create', 1, 1, 111),
('角色管理-编辑', 'system.role.update', '编辑角色信息', '系统管理', 'role', 'update', 1, 1, 112),
('角色管理-删除', 'system.role.delete', '删除角色', '系统管理', 'role', 'delete', 1, 1, 113),
('权限管理-查看', 'system.permission.read', '查看权限列表和详情', '系统管理', 'permission', 'read', 1, 1, 120),
('权限管理-创建', 'system.permission.create', '创建新权限', '系统管理', 'permission', 'create', 1, 1, 121),
('权限管理-编辑', 'system.permission.update', '编辑权限信息', '系统管理', 'permission', 'update', 1, 1, 122),
('权限管理-删除', 'system.permission.delete', '删除权限', '系统管理', 'permission', 'delete', 1, 1, 123),

-- 模型管理权限
('模型管理-查看', 'model.read', '查看模型列表和详情', '模型管理', 'model', 'read', 1, 1, 200),
('模型管理-创建', 'model.create', '创建新模型', '模型管理', 'model', 'create', 1, 1, 201),
('模型管理-编辑', 'model.update', '编辑模型信息', '模型管理', 'model', 'update', 1, 1, 202),
('模型管理-删除', 'model.delete', '删除模型', '模型管理', 'model', 'delete', 1, 1, 203),
('模型管理-部署', 'model.deploy', '部署模型', '模型管理', 'model', 'deploy', 1, 1, 204),

-- 数据集管理权限
('数据集管理-查看', 'dataset.read', '查看数据集列表和详情', '数据集管理', 'dataset', 'read', 1, 1, 300),
('数据集管理-创建', 'dataset.create', '创建新数据集', '数据集管理', 'dataset', 'create', 1, 1, 301),
('数据集管理-编辑', 'dataset.update', '编辑数据集信息', '数据集管理', 'dataset', 'update', 1, 1, 302),
('数据集管理-删除', 'dataset.delete', '删除数据集', '数据集管理', 'dataset', 'delete', 1, 1, 303),

-- 智能体管理权限
('智能体管理-查看', 'agent.read', '查看智能体列表和详情', '智能体管理', 'agent', 'read', 1, 1, 400),
('智能体管理-创建', 'agent.create', '创建新智能体', '智能体管理', 'agent', 'create', 1, 1, 401),
('智能体管理-编辑', 'agent.update', '编辑智能体信息', '智能体管理', 'agent', 'update', 1, 1, 402),
('智能体管理-删除', 'agent.delete', '删除智能体', '智能体管理', 'agent', 'delete', 1, 1, 403),
('智能体管理-执行', 'agent.execute', '执行智能体任务', '智能体管理', 'agent', 'execute', 1, 1, 404);

-- 为超级管理员角色分配所有权限
INSERT INTO `acwl_role_permissions` (`role_id`, `permission_id`)
SELECT 1, `id` FROM `acwl_permissions` WHERE `is_system` = 1;

-- 为管理员角色分配除系统管理外的权限
INSERT INTO `acwl_role_permissions` (`role_id`, `permission_id`)
SELECT 2, `id` FROM `acwl_permissions` WHERE `is_system` = 1 AND `module` != '系统管理';

-- 为普通用户角色分配基本查看和执行权限
INSERT INTO `acwl_role_permissions` (`role_id`, `permission_id`)
SELECT 3, `id` FROM `acwl_permissions` WHERE `is_system` = 1 AND `action` IN ('read', 'execute');

-- 为访客角色分配只读权限
INSERT INTO `acwl_role_permissions` (`role_id`, `permission_id`)
SELECT 4, `id` FROM `acwl_permissions` WHERE `is_system` = 1 AND `action` = 'read';