#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API使用日志表字段修正脚本

修正 api_usage_logs 表的字段名称和添加缺失字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def fix_api_usage_logs_table():
    """
    修正 api_usage_logs 表的字段
    """
    
    # 修正字段的 SQL 语句列表
    alter_statements = [
        # 重命名字段以匹配模型定义
        "ALTER TABLE `api_usage_logs` CHANGE COLUMN `request_ip` `client_ip` varchar(45) DEFAULT NULL COMMENT '客户端IP地址'",
        "ALTER TABLE `api_usage_logs` CHANGE COLUMN `request_method` `http_method` varchar(10) NOT NULL COMMENT 'HTTP方法'",
        "ALTER TABLE `api_usage_logs` CHANGE COLUMN `response_time` `processing_time` decimal(10,6) DEFAULT NULL COMMENT '处理时间（秒）'",
        
        # 修改字段类型以匹配模型定义
        "ALTER TABLE `api_usage_logs` MODIFY COLUMN `request_headers` json DEFAULT NULL COMMENT '请求头信息（JSON格式）'",
        "ALTER TABLE `api_usage_logs` MODIFY COLUMN `request_params` json DEFAULT NULL COMMENT '请求参数（JSON格式）'",
        "ALTER TABLE `api_usage_logs` MODIFY COLUMN `response_headers` json DEFAULT NULL COMMENT '响应头信息（JSON格式）'",
        "ALTER TABLE `api_usage_logs` MODIFY COLUMN `user_agent` varchar(500) DEFAULT NULL COMMENT '用户代理字符串'",
        
        # 添加缺失字段
        "ALTER TABLE `api_usage_logs` ADD COLUMN `error_traceback` longtext DEFAULT NULL COMMENT '错误堆栈信息' AFTER `error_message`",
        "ALTER TABLE `api_usage_logs` ADD COLUMN `data_size` int(11) DEFAULT NULL COMMENT '数据大小（字节）' AFTER `error_traceback`",
        "ALTER TABLE `api_usage_logs` ADD COLUMN `record_count` int(11) DEFAULT NULL COMMENT '处理记录数' AFTER `data_size`",
        "ALTER TABLE `api_usage_logs` ADD COLUMN `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER `created_at`",
        
        # 添加唯一索引
        "ALTER TABLE `api_usage_logs` ADD UNIQUE KEY `uk_request_id` (`request_id`)",
        
        # 添加复合索引
        "ALTER TABLE `api_usage_logs` ADD INDEX `idx_log_customer_created` (`customer_id`, `created_at`)",
        "ALTER TABLE `api_usage_logs` ADD INDEX `idx_log_api_created` (`api_id`, `created_at`)",
        "ALTER TABLE `api_usage_logs` ADD INDEX `idx_log_status_created` (`response_status`, `created_at`)",
        "ALTER TABLE `api_usage_logs` ADD INDEX `idx_log_ip_created` (`client_ip`, `created_at`)",
        "ALTER TABLE `api_usage_logs` ADD INDEX `idx_log_processing_time` (`processing_time`)",
    ]
    
    try:
        with engine.connect() as connection:
            print("正在修正 api_usage_logs 表...")
            
            for i, sql in enumerate(alter_statements, 1):
                try:
                    print(f"执行修改 {i}/{len(alter_statements)}: {sql[:50]}...")
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"  ✓ 修改 {i} 成功")
                except Exception as e:
                    if "Duplicate" in str(e) or "already exists" in str(e):
                        print(f"  - 修改 {i} 跳过（已存在）: {e}")
                    else:
                        print(f"  ✗ 修改 {i} 失败: {e}")
                        # 继续执行其他修改
                        continue
            
            print("\napi_usage_logs 表修正完成！")
            
            # 验证表结构
            result = connection.execute(text("DESCRIBE api_usage_logs"))
            columns = result.fetchall()
            print(f"\napi_usage_logs 表现在包含 {len(columns)} 个字段:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
                
    except Exception as e:
        print(f"修正 api_usage_logs 表时出错: {e}")
        raise

if __name__ == "__main__":
    print("开始 api_usage_logs 表字段修正...")
    fix_api_usage_logs_table()
    print("修正成功完成！")