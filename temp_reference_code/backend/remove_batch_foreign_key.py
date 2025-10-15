#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移除data_uploads表中batch_id字段的外键约束

根据业务需求，batch_id字段只作为标识字段使用，不需要外键约束。
这样可以避免在批次不存在时的外键约束错误。

Author: System
Date: 2025-07-18
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

def remove_batch_foreign_key():
    """
    移除data_uploads表中batch_id字段的外键约束
    """
    print("开始移除data_uploads表的batch_id外键约束...")
    
    try:
        with engine.connect() as connection:
            # 首先检查外键约束是否存在
            check_fk_sql = """
            SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'data_uploads' 
            AND COLUMN_NAME = 'batch_id' 
            AND REFERENCED_TABLE_NAME IS NOT NULL
            """
            
            result = connection.execute(text(check_fk_sql))
            foreign_keys = result.fetchall()
            
            if not foreign_keys:
                print("✓ data_uploads表的batch_id字段没有外键约束，无需操作")
                return
            
            print(f"发现 {len(foreign_keys)} 个外键约束需要移除:")
            for fk in foreign_keys:
                print(f"  - {fk[0]}")
            
            # 移除外键约束
            for fk in foreign_keys:
                constraint_name = fk[0]
                try:
                    print(f"移除外键约束: {constraint_name}")
                    drop_fk_sql = f"ALTER TABLE `data_uploads` DROP FOREIGN KEY `{constraint_name}`"
                    connection.execute(text(drop_fk_sql))
                    connection.commit()
                    print(f"✓ 成功移除外键约束: {constraint_name}")
                except Exception as e:
                    print(f"✗ 移除外键约束 {constraint_name} 失败: {e}")
                    continue
            
            # 验证外键约束是否已移除
            print("\n验证外键约束移除结果...")
            result = connection.execute(text(check_fk_sql))
            remaining_fks = result.fetchall()
            
            if not remaining_fks:
                print("✓ 所有batch_id相关的外键约束已成功移除")
            else:
                print(f"⚠ 仍有 {len(remaining_fks)} 个外键约束未移除:")
                for fk in remaining_fks:
                    print(f"  - {fk[0]}")
            
            # 检查表结构
            print("\n当前data_uploads表的batch_id字段信息:")
            column_info_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'data_uploads'
            AND COLUMN_NAME = 'batch_id'
            """
            
            result = connection.execute(text(column_info_sql))
            column_info = result.fetchone()
            
            if column_info:
                print(f"字段名: {column_info[0]}")
                print(f"数据类型: {column_info[1]}")
                print(f"允许NULL: {column_info[2]}")
                print(f"默认值: {column_info[3]}")
                print(f"注释: {column_info[4]}")
            
            print("\n✓ batch_id外键约束移除操作完成！")
            print("现在batch_id字段只作为标识字段使用，不再有外键约束限制。")
            
    except Exception as e:
        print(f"操作失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    remove_batch_foreign_key()