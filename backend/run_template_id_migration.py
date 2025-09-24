#!/usr/bin/env python3
"""
执行 template_id 字段迁移脚本
修复创建资源包时 template_id 为 null 导致的验证错误
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import sync_engine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """执行数据库迁移"""
    try:
        # 读取迁移脚本
        migration_file = "migrations/019_allow_null_template_id.sql"
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # 分割 SQL 语句（按分号分割）
        sql_statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        with sync_engine.begin() as conn:
            logger.info("开始执行 template_id 字段迁移...")
            
            for i, sql in enumerate(sql_statements, 1):
                if sql.strip():
                    logger.info(f"执行第 {i} 条 SQL 语句...")
                    logger.debug(f"SQL: {sql}")
                    
                    try:
                        result = conn.execute(text(sql))
                        
                        # 如果是查询语句，显示结果
                        if sql.strip().upper().startswith('SELECT'):
                            rows = result.fetchall()
                            if rows:
                                logger.info("查询结果:")
                                for row in rows:
                                    logger.info(f"  {dict(row)}")
                            else:
                                logger.info("  无结果")
                        else:
                            logger.info(f"  执行成功，影响行数: {result.rowcount if hasattr(result, 'rowcount') else 'N/A'}")
                            
                    except Exception as e:
                        logger.error(f"执行第 {i} 条 SQL 语句失败: {e}")
                        logger.error(f"SQL: {sql}")
                        # 继续执行其他语句
                        continue
            
            logger.info("✅ template_id 字段迁移完成！")
            
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        raise

if __name__ == "__main__":
    run_migration()