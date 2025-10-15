#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复customer_sessions表结构
添加缺失的created_at和updated_at字段
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def fix_customer_sessions_table():
    """
    修复customer_sessions表结构
    添加created_at和updated_at字段
    """
    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = 'acwl_api_system' "
                "AND TABLE_NAME = 'customer_sessions' "
                "AND COLUMN_NAME IN ('created_at', 'updated_at')"
            ))
            existing_columns = [row[0] for row in result.fetchall()]
            
            # 添加created_at字段（如果不存在）
            if 'created_at' not in existing_columns:
                print("添加created_at字段...")
                conn.execute(text(
                    "ALTER TABLE customer_sessions "
                    "ADD COLUMN created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'"
                ))
                print("✓ created_at字段添加成功")
            else:
                print("created_at字段已存在")
            
            # 添加updated_at字段（如果不存在）
            if 'updated_at' not in existing_columns:
                print("添加updated_at字段...")
                conn.execute(text(
                    "ALTER TABLE customer_sessions "
                    "ADD COLUMN updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP "
                    "ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'"
                ))
                print("✓ updated_at字段添加成功")
            else:
                print("updated_at字段已存在")
            
            # 提交事务
            conn.commit()
            
            # 验证表结构
            print("\n验证表结构:")
            result = conn.execute(text("DESCRIBE customer_sessions"))
            for row in result.fetchall():
                print(f"{row[0]}: {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}")
            
            print("\n✅ customer_sessions表结构修复完成！")
            
    except SQLAlchemyError as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始修复customer_sessions表结构...")
    success = fix_customer_sessions_table()
    
    if success:
        print("\n🎉 表结构修复成功！现在可以重新测试登录功能。")
    else:
        print("\n💥 表结构修复失败，请检查错误信息。")