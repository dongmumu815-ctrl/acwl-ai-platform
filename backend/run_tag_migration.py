#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行标签表数据库迁移脚本
为 acwl_data_resource_tags 表添加 created_by 和 updated_by 字段
"""

import pymysql
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings


def execute_migration():
    """执行数据库迁移"""
    
    # 读取迁移文件
    migration_file = Path(__file__).parent / "migrations" / "021_add_user_fields_to_data_resource_tags.sql"
    
    if not migration_file.exists():
        print(f"❌ 迁移文件不存在: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print(f"📄 读取迁移文件: {migration_file}")
    print(f"📝 迁移内容:\n{migration_sql}")
    
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET,
            autocommit=False
        )
        
        print(f"✅ 成功连接到数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        
        with connection.cursor() as cursor:
            # 首先检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'acwl_data_resource_tags'
            """, (settings.DB_NAME,))
            
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                print("❌ 表 acwl_data_resource_tags 不存在")
                return False
            
            print("✅ 表 acwl_data_resource_tags 存在")
            
            # 检查字段是否已经存在
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = 'acwl_data_resource_tags'
                AND COLUMN_NAME IN ('created_by', 'updated_by')
            """, (settings.DB_NAME,))
            
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            if 'created_by' in existing_columns and 'updated_by' in existing_columns:
                print("✅ 字段 created_by 和 updated_by 已经存在，跳过迁移")
                return True
            
            print(f"📊 现有字段: {existing_columns}")
            
            # 分割SQL语句并逐个执行
            sql_statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for i, statement in enumerate(sql_statements, 1):
                if statement.strip():
                    print(f"🔄 执行语句 {i}: {statement[:50]}...")
                    try:
                        cursor.execute(statement)
                        print(f"✅ 语句 {i} 执行成功")
                    except Exception as e:
                        print(f"❌ 语句 {i} 执行失败: {e}")
                        # 如果是字段已存在的错误，继续执行
                        if "Duplicate column name" in str(e):
                            print("⚠️  字段已存在，继续执行...")
                            continue
                        else:
                            raise e
            
            # 提交事务
            connection.commit()
            print("✅ 迁移执行成功，事务已提交")
            
            # 验证字段是否添加成功
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = 'acwl_data_resource_tags'
                AND COLUMN_NAME IN ('created_by', 'updated_by')
            """, (settings.DB_NAME,))
            
            new_columns = cursor.fetchall()
            print(f"📊 新添加的字段:")
            for col in new_columns:
                print(f"   - {col[0]}: {col[1]} (可空: {col[2]})")
            
            return True
            
    except Exception as e:
        print(f"❌ 迁移执行失败: {e}")
        if 'connection' in locals():
            connection.rollback()
            print("🔄 事务已回滚")
        return False
        
    finally:
        if 'connection' in locals():
            connection.close()
            print("🔌 数据库连接已关闭")


if __name__ == "__main__":
    print("🚀 开始执行标签表数据库迁移...")
    print("=" * 60)
    
    success = execute_migration()
    
    print("=" * 60)
    if success:
        print("🎉 迁移执行成功！")
        sys.exit(0)
    else:
        print("💥 迁移执行失败！")
        sys.exit(1)