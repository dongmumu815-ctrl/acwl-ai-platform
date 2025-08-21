#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 acwl_task_definitions 表结构
添加缺失的 workflow_id 和 workflow_node_id 字段
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import get_db, engine


async def check_and_add_columns():
    """检查并添加缺失的字段"""
    try:
        async with engine.begin() as conn:
            print("开始检查 acwl_task_definitions 表结构...")
            
            # 检查 workflow_id 字段是否存在
            result = await conn.execute(text("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'acwl_task_definitions' 
                AND COLUMN_NAME = 'workflow_id'
            """))
            
            workflow_id_exists = result.scalar() > 0
            print(f"workflow_id 字段存在: {workflow_id_exists}")
            
            if not workflow_id_exists:
                print("添加 workflow_id 字段...")
                await conn.execute(text("""
                    ALTER TABLE acwl_task_definitions 
                    ADD COLUMN workflow_id INT NULL 
                    COMMENT '所属工作流ID' 
                    AFTER project_id
                """))
                print("✅ workflow_id 字段添加成功")
            else:
                print("✅ workflow_id 字段已存在")
            
            # 检查 workflow_node_id 字段是否存在
            result = await conn.execute(text("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'acwl_task_definitions' 
                AND COLUMN_NAME = 'workflow_node_id'
            """))
            
            workflow_node_id_exists = result.scalar() > 0
            print(f"workflow_node_id 字段存在: {workflow_node_id_exists}")
            
            if not workflow_node_id_exists:
                print("添加 workflow_node_id 字段...")
                await conn.execute(text("""
                    ALTER TABLE acwl_task_definitions 
                    ADD COLUMN workflow_node_id INT NULL 
                    COMMENT '对应的工作流节点ID' 
                    AFTER workflow_id
                """))
                print("✅ workflow_node_id 字段添加成功")
            else:
                print("✅ workflow_node_id 字段已存在")
            
            # 检查并添加外键约束
            print("检查外键约束...")
            
            # 检查 workflow_id 外键约束
            result = await conn.execute(text("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'acwl_task_definitions' 
                AND CONSTRAINT_NAME LIKE '%workflow_id%'
                AND REFERENCED_TABLE_NAME = 'acwl_workflows'
            """))
            
            workflow_fk_exists = result.scalar() > 0
            print(f"workflow_id 外键约束存在: {workflow_fk_exists}")
            
            if not workflow_fk_exists and not workflow_id_exists:
                try:
                    print("添加 workflow_id 外键约束...")
                    await conn.execute(text("""
                        ALTER TABLE acwl_task_definitions 
                        ADD CONSTRAINT fk_task_definitions_workflow_id 
                        FOREIGN KEY (workflow_id) REFERENCES acwl_workflows(id) 
                        ON DELETE SET NULL
                    """))
                    print("✅ workflow_id 外键约束添加成功")
                except Exception as e:
                    print(f"⚠️ 添加 workflow_id 外键约束失败: {e}")
            
            # 检查 workflow_node_id 外键约束
            result = await conn.execute(text("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'acwl_task_definitions' 
                AND CONSTRAINT_NAME LIKE '%workflow_node_id%'
                AND REFERENCED_TABLE_NAME = 'acwl_workflow_nodes'
            """))
            
            workflow_node_fk_exists = result.scalar() > 0
            print(f"workflow_node_id 外键约束存在: {workflow_node_fk_exists}")
            
            if not workflow_node_fk_exists and not workflow_node_id_exists:
                try:
                    print("添加 workflow_node_id 外键约束...")
                    await conn.execute(text("""
                        ALTER TABLE acwl_task_definitions 
                        ADD CONSTRAINT fk_task_definitions_workflow_node_id 
                        FOREIGN KEY (workflow_node_id) REFERENCES acwl_workflow_nodes(id) 
                        ON DELETE SET NULL
                    """))
                    print("✅ workflow_node_id 外键约束添加成功")
                except Exception as e:
                    print(f"⚠️ 添加 workflow_node_id 外键约束失败: {e}")
            
            print("\n🎉 数据库结构修复完成！")
            
    except Exception as e:
        print(f"❌ 修复过程中发生错误: {e}")
        raise


async def main():
    """主函数"""
    print("=== 修复 acwl_task_definitions 表结构 ===")
    await check_and_add_columns()


if __name__ == "__main__":
    asyncio.run(main())