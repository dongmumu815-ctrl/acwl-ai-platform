#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复 task_type 枚举值问题
根据错误信息，数据库中的枚举定义可能仍然包含大写的 CUSTOM
需要将其修改为小写的 custom
"""

import pymysql
import sys

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '2wsx1QAZaczt',
    'database': 'acwl-ai-data',
    'charset': 'utf8mb4'
}

def fix_task_type_enum():
    """
    修复 task_type 枚举定义，确保所有值都是小写
    """
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("开始修复 task_type 枚举定义...")
        
        # 首先查看当前的枚举定义
        cursor.execute("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'acwl_ai_data' 
            AND TABLE_NAME = 'acwl_task_definitions' 
            AND COLUMN_NAME = 'task_type'
        """)
        
        current_def = cursor.fetchone()
        if current_def:
            print(f"当前枚举定义: {current_def[0]}")
        
        # 修改枚举定义，确保所有值都是小写
        print("\n修改枚举定义为小写值...")
        cursor.execute("""
            ALTER TABLE acwl_task_definitions 
            MODIFY COLUMN task_type ENUM(
                'data_sync',
                'model_train', 
                'data_analysis',
                'model_inference',
                'data_preprocessing',
                'model_evaluation',
                'data_visualization',
                'workflow_orchestration',
                'custom'
            ) NOT NULL DEFAULT 'custom'
        """)
        
        print("枚举定义修改完成!")
        
        # 确保所有数据都是小写
        print("\n更新所有大写的枚举值为小写...")
        
        # 更新可能的大写值
        updates = [
            ("UPDATE acwl_task_definitions SET task_type = 'data_sync' WHERE task_type = 'DATA_SYNC'", 'DATA_SYNC -> data_sync'),
            ("UPDATE acwl_task_definitions SET task_type = 'model_train' WHERE task_type = 'MODEL_TRAIN'", 'MODEL_TRAIN -> model_train'),
            ("UPDATE acwl_task_definitions SET task_type = 'data_analysis' WHERE task_type = 'DATA_ANALYSIS'", 'DATA_ANALYSIS -> data_analysis'),
            ("UPDATE acwl_task_definitions SET task_type = 'model_inference' WHERE task_type = 'MODEL_INFERENCE'", 'MODEL_INFERENCE -> model_inference'),
            ("UPDATE acwl_task_definitions SET task_type = 'data_preprocessing' WHERE task_type = 'DATA_PREPROCESSING'", 'DATA_PREPROCESSING -> data_preprocessing'),
            ("UPDATE acwl_task_definitions SET task_type = 'model_evaluation' WHERE task_type = 'MODEL_EVALUATION'", 'MODEL_EVALUATION -> model_evaluation'),
            ("UPDATE acwl_task_definitions SET task_type = 'data_visualization' WHERE task_type = 'DATA_VISUALIZATION'", 'DATA_VISUALIZATION -> data_visualization'),
            ("UPDATE acwl_task_definitions SET task_type = 'workflow_orchestration' WHERE task_type = 'WORKFLOW_ORCHESTRATION'", 'WORKFLOW_ORCHESTRATION -> workflow_orchestration'),
            ("UPDATE acwl_task_definitions SET task_type = 'custom' WHERE task_type = 'CUSTOM'", 'CUSTOM -> custom')
        ]
        
        total_updated = 0
        for update_sql, description in updates:
            cursor.execute(update_sql)
            affected = cursor.rowcount
            if affected > 0:
                print(f"  {description}: {affected} 条记录")
                total_updated += affected
        
        if total_updated == 0:
            print("  没有需要更新的记录")
        else:
            print(f"  总共更新了 {total_updated} 条记录")
        
        # 提交更改
        connection.commit()
        
        # 验证修改结果
        print("\n验证修改结果...")
        cursor.execute("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'acwl_ai_data' 
            AND TABLE_NAME = 'acwl_task_definitions' 
            AND COLUMN_NAME = 'task_type'
        """)
        
        new_def = cursor.fetchone()
        if new_def:
            print(f"新的枚举定义: {new_def[0]}")
        
        # 查询当前的值分布
        cursor.execute("""
            SELECT DISTINCT task_type, COUNT(*) as count
            FROM acwl_task_definitions 
            GROUP BY task_type
            ORDER BY task_type
        """)
        
        values = cursor.fetchall()
        print("\n当前 task_type 值分布:")
        for value, count in values:
            print(f"  {value}: {count} 条记录")
        
        cursor.close()
        connection.close()
        
        print("\n修复完成!")
        
    except Exception as e:
        print(f"错误: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        sys.exit(1)

if __name__ == "__main__":
    fix_task_type_enum()