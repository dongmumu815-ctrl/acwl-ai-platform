#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from app.core.database import engine
from sqlalchemy import text

async def add_missing_fields():
    """添加执行器节点表缺失的字段"""
    async with engine.begin() as conn:
        # 添加缺失的字段
        migrations = [
            "ALTER TABLE acwl_executor_nodes ADD COLUMN supported_task_types JSON COMMENT '支持的任务类型' AFTER version",
            "ALTER TABLE acwl_executor_nodes ADD COLUMN resource_capacity JSON COMMENT '资源容量' AFTER supported_task_types",
            "ALTER TABLE acwl_executor_nodes ADD COLUMN resource_usage JSON COMMENT '当前资源使用情况' AFTER resource_capacity",
            "ALTER TABLE acwl_executor_nodes ADD COLUMN total_tasks_executed INT DEFAULT 0 COMMENT '总执行任务数' AFTER current_load",
            "ALTER TABLE acwl_executor_nodes ADD COLUMN tags JSON COMMENT '标签' AFTER registration_time",
            "ALTER TABLE acwl_executor_nodes ADD COLUMN node_metadata JSON COMMENT '节点元数据' AFTER tags"
        ]
        
        for migration in migrations:
            try:
                await conn.execute(text(migration))
                print(f"执行成功: {migration}")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"字段已存在，跳过: {migration}")
                else:
                    print(f"执行失败: {migration}, 错误: {e}")
        
        # 重命名字段
        try:
            await conn.execute(text("ALTER TABLE acwl_executor_nodes CHANGE COLUMN metadata node_metadata_old JSON"))
            print("重命名 metadata 字段成功")
        except Exception as e:
            print(f"重命名 metadata 字段失败: {e}")
        
        print("数据库迁移完成")

if __name__ == "__main__":
    asyncio.run(add_missing_fields())