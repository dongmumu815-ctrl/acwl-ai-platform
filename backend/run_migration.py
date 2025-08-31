#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行数据库迁移脚本
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from app.core.database import get_db


async def run_migration(migration_file: str):
    """
    运行指定的迁移文件
    
    Args:
        migration_file: 迁移文件路径
    """
    try:
        # 读取迁移文件内容
        migration_path = Path(migration_file)
        if not migration_path.exists():
            print(f"迁移文件不存在: {migration_file}")
            return False
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"开始执行迁移: {migration_file}")
        
        # 获取数据库会话并执行迁移
        async for db in get_db():
            try:
                # 分割SQL语句并逐个执行
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for i, statement in enumerate(statements, 1):
                    if statement:
                        print(f"执行语句 {i}/{len(statements)}: {statement[:50]}...")
                        await db.execute(text(statement))
                
                await db.commit()
                print(f"迁移执行成功: {migration_file}")
                return True
                
            except Exception as e:
                await db.rollback()
                print(f"迁移执行失败: {e}")
                return False
            finally:
                await db.close()
                
    except Exception as e:
        print(f"读取迁移文件失败: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python run_migration.py <migration_file>")
        print("示例: python run_migration.py migrations/006_add_model_service_config.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    success = asyncio.run(run_migration(migration_file))
    
    if success:
        print("迁移完成")
        sys.exit(0)
    else:
        print("迁移失败")
        sys.exit(1)