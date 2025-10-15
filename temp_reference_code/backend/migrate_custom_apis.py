#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义API表迁移脚本

为 custom_apis 表添加缺失的字段：
- require_authentication: 是否需要认证
- response_format: 响应格式
- total_calls: 总调用次数
- last_called_at: 最后调用时间
"""

import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine

def migrate_custom_apis_table():
    """
    执行 custom_apis 表的数据库迁移
    
    Returns:
        bool: 迁移是否成功
    """
    try:
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                print("开始迁移 custom_apis 表...")
                
                # 检查字段是否已存在
                check_columns_sql = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'acwl_api_system' 
                    AND TABLE_NAME = 'custom_apis'
                    AND COLUMN_NAME IN ('require_authentication', 'response_format', 'total_calls', 'last_called_at')
                """
                
                result = connection.execute(text(check_columns_sql))
                existing_columns = [row[0] for row in result.fetchall()]
                
                print(f"已存在的字段: {existing_columns}")
                
                # 需要添加的字段
                fields_to_add = {
                    'require_authentication': "ADD COLUMN `require_authentication` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否需要认证：1-需要，0-不需要'",
                    'response_format': "ADD COLUMN `response_format` enum('JSON','XML','TEXT') NOT NULL DEFAULT 'JSON' COMMENT '响应格式'",
                    'total_calls': "ADD COLUMN `total_calls` int(11) NOT NULL DEFAULT 0 COMMENT '总调用次数'",
                    'last_called_at': "ADD COLUMN `last_called_at` timestamp NULL DEFAULT NULL COMMENT '最后调用时间'"
                }
                
                # 添加缺失的字段
                for field_name, alter_sql in fields_to_add.items():
                    if field_name not in existing_columns:
                        print(f"添加字段: {field_name}")
                        connection.execute(text(f"ALTER TABLE `custom_apis` {alter_sql}"))
                    else:
                        print(f"字段 {field_name} 已存在，跳过")
                
                # 添加索引（如果不存在）
                indexes_to_add = [
                    ("idx_custom_apis_require_auth", "CREATE INDEX `idx_custom_apis_require_auth` ON `custom_apis`(`require_authentication`)"),
                    ("idx_custom_apis_response_format", "CREATE INDEX `idx_custom_apis_response_format` ON `custom_apis`(`response_format`)"),
                    ("idx_custom_apis_total_calls", "CREATE INDEX `idx_custom_apis_total_calls` ON `custom_apis`(`total_calls`)"),
                    ("idx_custom_apis_last_called", "CREATE INDEX `idx_custom_apis_last_called` ON `custom_apis`(`last_called_at`)")
                ]
                
                for index_name, create_sql in indexes_to_add:
                    try:
                        print(f"创建索引: {index_name}")
                        connection.execute(text(create_sql))
                    except SQLAlchemyError as e:
                        if "Duplicate key name" in str(e) or "already exists" in str(e):
                            print(f"索引 {index_name} 已存在，跳过")
                        else:
                            print(f"创建索引 {index_name} 失败: {e}")
                
                # 验证迁移结果
                verify_sql = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'acwl_api_system' 
                    AND TABLE_NAME = 'custom_apis'
                    AND COLUMN_NAME IN ('require_authentication', 'response_format', 'total_calls', 'last_called_at')
                ORDER BY ORDINAL_POSITION
                """
                
                result = connection.execute(text(verify_sql))
                columns = result.fetchall()
                
                print("\n迁移后的字段信息:")
                for column in columns:
                    print(f"  {column[0]}: {column[1]} (可空: {column[2]}, 默认值: {column[3]})")
                
                # 提交事务
                trans.commit()
                print("\ncustom_apis 表迁移完成！")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"迁移失败，已回滚: {e}")
                return False
                
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    print("开始执行 custom_apis 表迁移...")
    success = migrate_custom_apis_table()
    
    if success:
        print("迁移成功完成！")
        sys.exit(0)
    else:
        print("迁移失败！")
        sys.exit(1)