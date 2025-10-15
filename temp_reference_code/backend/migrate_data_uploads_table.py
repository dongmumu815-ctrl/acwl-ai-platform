#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据上传表迁移脚本

为 data_uploads 表添加缺失的字段，使其与模型定义保持一致

Author: System
Date: 2025-07-15
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

def migrate_data_uploads_table():
    """
    为 data_uploads 表添加缺失的字段
    """
    print("开始 data_uploads 表迁移...")
    
    # 定义需要的字段及其SQL定义
    required_fields = {
        'usage_log_id': "ADD COLUMN `usage_log_id` bigint(20) unsigned DEFAULT NULL COMMENT '关联的使用日志ID' AFTER `api_id`",
        'upload_id': "ADD COLUMN `upload_id` varchar(64) NOT NULL COMMENT '上传唯一标识' AFTER `usage_log_id`",
        'original_filename': "ADD COLUMN `original_filename` varchar(255) DEFAULT NULL COMMENT '原始文件名' AFTER `batch_id`",
        'file_path': "ADD COLUMN `file_path` varchar(500) DEFAULT NULL COMMENT '文件存储路径' AFTER `original_filename`",
        'file_size': "ADD COLUMN `file_size` int(11) DEFAULT NULL COMMENT '文件大小（字节）' AFTER `file_path`",
        'file_type': "ADD COLUMN `file_type` varchar(50) DEFAULT NULL COMMENT '文件类型' AFTER `file_size`",
        'data_content': "ADD COLUMN `data_content` longtext DEFAULT NULL COMMENT '数据内容（JSON格式）' AFTER `file_type`",
        'status': "ADD COLUMN `status` enum('pending','processing','completed','failed') NOT NULL DEFAULT 'pending' COMMENT '处理状态' AFTER `data_content`",
        'processed_at': "ADD COLUMN `processed_at` timestamp NULL DEFAULT NULL COMMENT '处理完成时间' AFTER `status`",
        'processing_time': "ADD COLUMN `processing_time` decimal(10,6) DEFAULT NULL COMMENT '处理时间（秒）' AFTER `processed_at`",
        'record_count': "ADD COLUMN `record_count` int(11) DEFAULT NULL COMMENT '记录数量' AFTER `processing_time`",
        'error_message': "ADD COLUMN `error_message` text DEFAULT NULL COMMENT '错误信息' AFTER `validation_errors`",
        'meta_data': "ADD COLUMN `meta_data` json DEFAULT NULL COMMENT '元数据' AFTER `error_message`",
        'updated_at': "ADD COLUMN `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER `created_at`"
    }
    
    try:
        with engine.connect() as connection:
            # 检查当前表结构
            check_sql = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'data_uploads'
            """
            
            result = connection.execute(text(check_sql))
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"当前字段: {existing_columns}")
            
            # 找出缺失的字段
            missing_fields = []
            for field_name, field_sql in required_fields.items():
                if field_name not in existing_columns:
                    missing_fields.append((field_name, field_sql))
            
            if not missing_fields:
                print("所有必需字段都已存在，无需迁移")
                return
            
            print(f"需要添加的字段: {[field[0] for field in missing_fields]}")
            
            # 逐个添加缺失的字段
            for field_name, field_sql in missing_fields:
                try:
                    print(f"添加字段: {field_name}")
                    connection.execute(text(f"ALTER TABLE `data_uploads` {field_sql}"))
                    connection.commit()
                    print(f"✓ 成功添加字段: {field_name}")
                except Exception as e:
                    print(f"✗ 添加字段 {field_name} 失败: {e}")
                    # 继续添加其他字段
                    continue
            
            # 添加外键约束（如果 usage_log_id 字段被添加）
            if 'usage_log_id' in [field[0] for field in missing_fields]:
                try:
                    print("添加外键约束...")
                    foreign_key_sql = """
                    ALTER TABLE `data_uploads` 
                    ADD CONSTRAINT `fk_data_uploads_usage_log` 
                    FOREIGN KEY (`usage_log_id`) REFERENCES `api_usage_logs`(`id`) ON DELETE SET NULL
                    """
                    connection.execute(text(foreign_key_sql))
                    connection.commit()
                    print("✓ 成功添加外键约束")
                except Exception as e:
                    print(f"添加外键约束失败（可忽略）: {e}")
            
            # 添加索引
            indexes = [
                ("uk_upload_id", "ADD UNIQUE INDEX `uk_upload_id` (`upload_id`)"),
                ("idx_upload_usage_log", "ADD INDEX `idx_upload_usage_log` (`usage_log_id`)"),
                ("idx_upload_customer_created", "ADD INDEX `idx_upload_customer_created` (`customer_id`, `created_at`)"),
                ("idx_upload_api_created", "ADD INDEX `idx_upload_api_created` (`api_id`, `created_at`)"),
                ("idx_upload_status_created", "ADD INDEX `idx_upload_status_created` (`status`, `created_at`)"),
                ("idx_upload_batch", "ADD INDEX `idx_upload_batch` (`batch_id`)")
            ]
            
            print("添加索引...")
            for index_name, index_sql in indexes:
                try:
                    connection.execute(text(f"ALTER TABLE `data_uploads` {index_sql}"))
                    connection.commit()
                    print(f"✓ 成功添加索引: {index_name}")
                except Exception as e:
                    if "Duplicate key name" in str(e) or "already exists" in str(e):
                        print(f"索引 {index_name} 已存在，跳过")
                    else:
                        print(f"添加索引 {index_name} 失败: {e}")
            
            # 验证最终表结构
            print("\n验证表结构...")
            verify_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'data_uploads'
            ORDER BY ORDINAL_POSITION
            """
            
            result = connection.execute(text(verify_sql))
            columns = result.fetchall()
            
            print("\n当前 data_uploads 表结构:")
            print("-" * 100)
            print(f"{'字段名':<25} {'类型':<20} {'允许NULL':<10} {'默认值':<20} {'注释':<30}")
            print("-" * 100)
            for col in columns:
                print(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {str(col[3]):<20} {(col[4] or '')[:30]:<30}")
            
            print(f"\n✓ data_uploads 表迁移完成！总共 {len(columns)} 个字段")
            
    except Exception as e:
        print(f"迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_data_uploads_table()