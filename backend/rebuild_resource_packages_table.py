#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源包表完整重构脚本
删除旧的resource_packages表，创建优化的新表结构
"""

import asyncio
import logging
import sys
sys.path.append('.')
from sqlalchemy import text

from app.core.database import get_db_context

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def backup_existing_data():
    """备份现有数据（可选）"""
    async with get_db_context() as db:
        try:
            # 检查表是否存在
            result = await db.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'resource_packages'
            """))
            
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                logger.info("resource_packages表不存在，跳过备份")
                return
            
            # 检查是否有数据
            result = await db.execute(text("SELECT COUNT(*) FROM resource_packages"))
            data_count = result.fetchone()[0]
            
            if data_count == 0:
                logger.info("resource_packages表为空，跳过备份")
                return
            
            logger.info(f"发现 {data_count} 条记录，创建备份表...")
            
            # 先删除已存在的备份表
            await db.execute(text("DROP TABLE IF EXISTS resource_packages_backup_20240923"))
            
            # 创建备份表
            await db.execute(text("""
                CREATE TABLE resource_packages_backup_20240923 AS 
                SELECT * FROM resource_packages
            """))
            
            logger.info(f"✅ 成功备份 {data_count} 条记录到 resource_packages_backup_20240923")
            
        except Exception as e:
            logger.error(f"备份数据时出错: {str(e)}")
            raise

async def drop_existing_table():
    """删除现有的resource_packages表及其依赖表"""
    async with get_db_context() as db:
        try:
            # 先删除依赖表
            logger.info("删除依赖表...")
            
            dependent_tables = [
                'resource_package_query_history',
                'resource_package_permissions',
                'resource_package_tags'
            ]
            
            for table in dependent_tables:
                try:
                    await db.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    logger.info(f"✅ 删除依赖表: {table}")
                except Exception as e:
                    logger.warning(f"删除依赖表 {table} 失败: {str(e)}")
            
            # 删除主表
            await db.execute(text("DROP TABLE IF EXISTS resource_packages"))
            logger.info("✅ 成功删除旧的resource_packages表")
            
        except Exception as e:
            logger.error(f"删除表时出错: {str(e)}")
            raise

async def create_optimized_table():
    """创建优化后的resource_packages表"""
    async with get_db_context() as db:
        try:
            logger.info("创建优化后的resource_packages表...")
            
            create_table_sql = """
            CREATE TABLE `resource_packages` (
                `id` int NOT NULL AUTO_INCREMENT,
                `name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源包名称',
                `description` text COLLATE utf8mb4_general_ci COMMENT '资源包描述',
                `type` enum('sql','elasticsearch') COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源包类型',
                
                -- 核心关联字段
                `template_id` int NOT NULL COMMENT '关联的查询模板ID',
                `template_type` enum('sql','elasticsearch') COLLATE utf8mb4_general_ci NOT NULL COMMENT '模板类型',
                `dynamic_params` json DEFAULT NULL COMMENT '动态参数配置，用于覆盖模板中的参数',
                
                -- 保留的业务字段（用于快速筛选和权限控制）
                `datasource_id` int NOT NULL COMMENT '数据源ID（冗余字段，用于快速筛选）',
                `resource_id` int DEFAULT NULL COMMENT '数据资源ID（业务关联）',
                
                -- 系统字段
                `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
                `created_by` int NOT NULL COMMENT '创建者ID',
                `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                
                PRIMARY KEY (`id`),
                KEY `idx_template_id` (`template_id`),
                KEY `idx_template_type` (`template_type`),
                KEY `idx_datasource_id` (`datasource_id`),
                KEY `idx_resource_id` (`resource_id`),
                KEY `idx_created_by` (`created_by`),
                KEY `idx_type` (`type`),
                KEY `idx_name` (`name`),
                KEY `idx_active` (`is_active`),
                KEY `idx_created_at` (`created_at`),
                
                -- 外键约束
                CONSTRAINT `fk_resource_packages_datasource` FOREIGN KEY (`datasource_id`) REFERENCES `acwl_datasources` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_resource_packages_resource` FOREIGN KEY (`resource_id`) REFERENCES `acwl_data_resources` (`id`) ON DELETE SET NULL,
                CONSTRAINT `fk_resource_packages_creator` FOREIGN KEY (`created_by`) REFERENCES `acwl_users` (`id`) ON DELETE CASCADE,
                
                -- 数据一致性约束
                CONSTRAINT `chk_template_consistency` CHECK (
                    (template_type = 'sql' AND template_id IS NOT NULL) OR
                    (template_type = 'elasticsearch' AND template_id IS NOT NULL)
                ),
                CONSTRAINT `chk_type_template_match` CHECK (type = template_type)
                
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='资源包表（优化版）';
            """
            
            await db.execute(text(create_table_sql))
            logger.info("✅ 成功创建优化后的resource_packages表")
            
        except Exception as e:
            logger.error(f"创建表时出错: {str(e)}")
            raise

async def recreate_dependent_tables():
    """重新创建依赖表"""
    async with get_db_context() as db:
        try:
            logger.info("重新创建依赖表...")
            
            # 创建资源包权限表
            permissions_table_sql = """
            CREATE TABLE `resource_package_permissions` (
                `id` int NOT NULL AUTO_INCREMENT,
                `package_id` int NOT NULL COMMENT '资源包ID',
                `user_id` int NOT NULL COMMENT '用户ID',
                `permission_type` enum('read','write','admin') COLLATE utf8mb4_general_ci NOT NULL COMMENT '权限类型',
                `granted_by` int NOT NULL COMMENT '授权者ID',
                `granted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                `expires_at` timestamp NULL DEFAULT NULL COMMENT '过期时间',
                `is_active` tinyint(1) DEFAULT 1 COMMENT '是否有效',
                
                PRIMARY KEY (`id`),
                UNIQUE KEY `uk_package_user` (`package_id`,`user_id`),
                KEY `idx_package_id` (`package_id`),
                KEY `idx_user_id` (`user_id`),
                KEY `idx_permission_type` (`permission_type`),
                KEY `idx_granted_by` (`granted_by`),
                KEY `idx_expires_at` (`expires_at`),
                
                CONSTRAINT `fk_permissions_package` FOREIGN KEY (`package_id`) REFERENCES `resource_packages` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_permissions_user` FOREIGN KEY (`user_id`) REFERENCES `acwl_users` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_permissions_granter` FOREIGN KEY (`granted_by`) REFERENCES `acwl_users` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='资源包权限表';
            """
            
            await db.execute(text(permissions_table_sql))
            logger.info("✅ 创建resource_package_permissions表")
            
            # 创建资源包查询历史表
            history_table_sql = """
            CREATE TABLE `resource_package_query_history` (
                `id` int NOT NULL AUTO_INCREMENT,
                `package_id` int NOT NULL COMMENT '资源包ID',
                `user_id` int NOT NULL COMMENT '查询用户ID',
                `dynamic_params` json DEFAULT NULL COMMENT '动态参数值',
                `generated_query` text COLLATE utf8mb4_general_ci COMMENT '生成的查询语句',
                `result_count` int DEFAULT 0 COMMENT '结果行数',
                `execution_time` int DEFAULT 0 COMMENT '执行时间(毫秒)',
                `status` enum('success','error','timeout') COLLATE utf8mb4_general_ci DEFAULT 'success' COMMENT '执行状态',
                `error_message` text COLLATE utf8mb4_general_ci COMMENT '错误信息',
                `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (`id`),
                KEY `idx_package_id` (`package_id`),
                KEY `idx_user_id` (`user_id`),
                KEY `idx_status` (`status`),
                KEY `idx_created_at` (`created_at`),
                
                CONSTRAINT `fk_history_package` FOREIGN KEY (`package_id`) REFERENCES `resource_packages` (`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_history_user` FOREIGN KEY (`user_id`) REFERENCES `acwl_users` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='资源包查询历史表';
            """
            
            await db.execute(text(history_table_sql))
            logger.info("✅ 创建resource_package_query_history表")
            
            # 创建资源包标签关联表
            tags_table_sql = """
            CREATE TABLE `resource_package_tags` (
                `id` int NOT NULL AUTO_INCREMENT,
                `package_id` int NOT NULL COMMENT '资源包ID',
                `tag_name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL COMMENT '标签名称',
                `tag_color` varchar(20) COLLATE utf8mb4_general_ci DEFAULT '#409EFF' COMMENT '标签颜色',
                `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                
                PRIMARY KEY (`id`),
                UNIQUE KEY `uk_package_tag` (`package_id`,`tag_name`),
                KEY `idx_package_id` (`package_id`),
                KEY `idx_tag_name` (`tag_name`),
                
                CONSTRAINT `fk_tags_package` FOREIGN KEY (`package_id`) REFERENCES `resource_packages` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='资源包标签关联表';
            """
            
            await db.execute(text(tags_table_sql))
            logger.info("✅ 创建resource_package_tags表")
            
        except Exception as e:
            logger.error(f"创建依赖表时出错: {str(e)}")
            raise

async def verify_table_structure():
    """验证新表结构"""
    async with get_db_context() as db:
        try:
            logger.info("验证新表结构...")
            
            # 检查表结构
            result = await db.execute(text("""
                DESCRIBE resource_packages
            """))
            
            columns = result.fetchall()
            logger.info("新表字段结构:")
            for column in columns:
                logger.info(f"  - {column[0]}: {column[1]} {column[2]} {column[3]} {column[4]} {column[5]}")
            
            # 检查索引
            result = await db.execute(text("""
                SHOW INDEX FROM resource_packages
            """))
            
            indexes = result.fetchall()
            logger.info("表索引:")
            for index in indexes:
                logger.info(f"  - {index[2]}: {index[4]} ({index[10]})")
            
            # 检查约束
            result = await db.execute(text("""
                SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE 
                FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'resource_packages'
            """))
            
            constraints = result.fetchall()
            logger.info("表约束:")
            for constraint in constraints:
                logger.info(f"  - {constraint[0]}: {constraint[1]}")
            
            logger.info("✅ 表结构验证完成")
            
        except Exception as e:
            logger.error(f"验证表结构时出错: {str(e)}")
            raise

async def main():
    """主函数"""
    try:
        logger.info("开始资源包表重构...")
        
        # 步骤1: 备份现有数据
        logger.info("步骤1: 备份现有数据")
        await backup_existing_data()
        
        # 步骤2: 删除现有表
        logger.info("步骤2: 删除现有表")
        await drop_existing_table()
        
        # 步骤3: 创建优化后的表
        logger.info("步骤3: 创建优化后的表")
        await create_optimized_table()
        
        # 步骤4: 重新创建依赖表
        logger.info("步骤4: 重新创建依赖表")
        await recreate_dependent_tables()
        
        # 步骤5: 验证表结构
        logger.info("步骤5: 验证表结构")
        await verify_table_structure()
        
        print("\n" + "="*60)
        print("🎉 资源包表重构完成！")
        print("="*60)
        print("✅ 已删除旧的resource_packages表")
        print("✅ 已创建优化后的resource_packages表")
        print("✅ 移除了冗余字段：base_config, locked_conditions, dynamic_conditions, order_config")
        print("✅ 保留了关键字段：datasource_id, resource_id（用于快速筛选和业务关联）")
        print("✅ 添加了新的核心字段：template_id, template_type, dynamic_params")
        print("✅ 优化了索引和约束")
        print("\n📋 下一步需要:")
        print("1. 更新ResourcePackage模型")
        print("2. 更新相关API和服务代码")
        print("3. 更新前端接口定义")
        
    except Exception as e:
        logger.error(f"重构过程中发生错误: {str(e)}")
        print(f"\n❌ 重构失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())