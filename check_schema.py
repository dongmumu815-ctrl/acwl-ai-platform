#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库schema和枚举定义
"""

import pymysql

# 数据库配置
DB_CONFIG = {
    'host': '10.20.1.200',
    'port': 3306,
    'user': 'root',
    'password': '2wsx1QAZaczt',
    'database': 'acwl-ai'
}

def check_schema():
    """
    检查数据库schema和枚举定义
    """
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4'
        )
        
        print("✅ 数据库连接成功")
        
        with connection.cursor() as cursor:
            # 检查表结构
            cursor.execute("SHOW CREATE TABLE acwl_models")
            result = cursor.fetchone()
            print(f"\n表结构:")
            print(result[1])
            
            # 检查列信息
            cursor.execute("SHOW COLUMNS FROM acwl_models LIKE 'model_type'")
            column_info = cursor.fetchone()
            print(f"\nmodel_type列信息:")
            print(f"Field: {column_info[0]}")
            print(f"Type: {column_info[1]}")
            print(f"Null: {column_info[2]}")
            print(f"Key: {column_info[3]}")
            print(f"Default: {column_info[4]}")
            print(f"Extra: {column_info[5]}")
            
            # 尝试直接修改枚举定义
            print("\n尝试修改枚举定义...")
            alter_sql = """
            ALTER TABLE acwl_models 
            MODIFY COLUMN model_type ENUM('LLM', 'EMBEDDING', 'MULTIMODAL', 'OTHER', 'Embedding', 'Multimodal', 'Other') NOT NULL
            """
            cursor.execute(alter_sql)
            print("✅ 枚举定义已修改，现在包含新旧格式")
            
            # 现在更新数据
            cursor.execute("UPDATE acwl_models SET model_type = 'EMBEDDING' WHERE model_type = 'Embedding'")
            affected_rows = cursor.rowcount
            print(f"✅ 更新Embedding -> EMBEDDING: {affected_rows} 条记录")
            
            cursor.execute("UPDATE acwl_models SET model_type = 'MULTIMODAL' WHERE model_type = 'Multimodal'")
            affected_rows = cursor.rowcount
            print(f"✅ 更新Multimodal -> MULTIMODAL: {affected_rows} 条记录")
            
            cursor.execute("UPDATE acwl_models SET model_type = 'OTHER' WHERE model_type = 'Other'")
            affected_rows = cursor.rowcount
            print(f"✅ 更新Other -> OTHER: {affected_rows} 条记录")
            
            # 最后移除旧的枚举值
            final_alter_sql = """
            ALTER TABLE acwl_models 
            MODIFY COLUMN model_type ENUM('LLM', 'EMBEDDING', 'MULTIMODAL', 'OTHER') NOT NULL
            """
            cursor.execute(final_alter_sql)
            print("✅ 最终枚举定义已设置")
            
            # 提交更改
            connection.commit()
            print("\n✅ 所有更改已提交")
            
            # 验证结果
            cursor.execute("SELECT id, name, model_type FROM acwl_models")
            models = cursor.fetchall()
            print(f"\n最终模型数据:")
            for model in models:
                print(f"ID: {model[0]}, Name: {model[1]}, Type: {model[2]}")
                
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    check_schema()