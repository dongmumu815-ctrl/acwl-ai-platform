#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加缺失的字段到 api_usage_logs 表

根据错误日志，数据库表中缺少以下字段：
- timestamp
- nonce
- encrypted_data
- iv
- signature
- needread
- is_encrypted
"""

import pymysql
from app.core.config import settings

def add_missing_fields():
    """
    添加缺失的字段到 api_usage_logs 表
    """
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("开始检查和添加缺失的字段...")
        
        # 检查表结构
        cursor.execute("DESCRIBE api_usage_logs")
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"现有字段: {existing_columns}")
        
        # 需要添加的字段定义
        fields_to_add = [
            {
                'name': 'timestamp',
                'definition': 'BIGINT NULL COMMENT "请求时间戳（用于防重放攻击）"'
            },
            {
                'name': 'nonce',
                'definition': 'VARCHAR(32) NULL COMMENT "随机字符串（用于增强请求唯一性）"'
            },
            {
                'name': 'encrypted_data',
                'definition': 'LONGTEXT NULL COMMENT "加密后的业务数据（Base64编码）"'
            },
            {
                'name': 'iv',
                'definition': 'VARCHAR(64) NULL COMMENT "初始化向量（IV），用于AES解密"'
            },
            {
                'name': 'signature',
                'definition': 'VARCHAR(128) NULL COMMENT "数据签名值（HMAC-SHA256）"'
            },
            {
                'name': 'needread',
                'definition': 'BOOLEAN NULL DEFAULT FALSE COMMENT "是否需要读取确认"'
            },
            {
                'name': 'is_encrypted',
                'definition': 'BOOLEAN NULL DEFAULT FALSE COMMENT "是否为加密请求"'
            }
        ]
        
        # 添加缺失的字段
        for field in fields_to_add:
            if field['name'] not in existing_columns:
                sql = f"ALTER TABLE api_usage_logs ADD COLUMN {field['name']} {field['definition']}"
                print(f"添加字段: {field['name']}")
                print(f"SQL: {sql}")
                cursor.execute(sql)
                print(f"✅ 成功添加字段: {field['name']}")
            else:
                print(f"⚠️ 字段已存在: {field['name']}")
        
        # 添加索引
        indexes_to_add = [
            {
                'name': 'idx_log_timestamp',
                'sql': 'CREATE INDEX idx_log_timestamp ON api_usage_logs (timestamp)'
            },
            {
                'name': 'idx_log_nonce',
                'sql': 'CREATE INDEX idx_log_nonce ON api_usage_logs (nonce)'
            },
            {
                'name': 'idx_log_encrypted',
                'sql': 'CREATE INDEX idx_log_encrypted ON api_usage_logs (is_encrypted)'
            }
        ]
        
        print("\n开始添加索引...")
        for index in indexes_to_add:
            try:
                cursor.execute(index['sql'])
                print(f"✅ 成功添加索引: {index['name']}")
            except pymysql.err.OperationalError as e:
                if "Duplicate key name" in str(e):
                    print(f"⚠️ 索引已存在: {index['name']}")
                else:
                    print(f"❌ 添加索引失败: {index['name']}, 错误: {e}")
        
        # 提交更改
        connection.commit()
        print("\n✅ 所有更改已提交")
        
        # 验证表结构
        cursor.execute("DESCRIBE api_usage_logs")
        final_columns = [row[0] for row in cursor.fetchall()]
        print(f"\n最终字段列表: {final_columns}")
        
        # 检查缺失的字段
        missing_fields = [field['name'] for field in fields_to_add if field['name'] not in final_columns]
        if missing_fields:
            print(f"❌ 仍然缺失的字段: {missing_fields}")
        else:
            print("✅ 所有必需字段都已添加")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    add_missing_fields()