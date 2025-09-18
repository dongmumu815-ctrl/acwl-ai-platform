#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彻底修复 task_type 枚举值问题
确保数据库中的枚举定义与代码中的 TaskType 枚举一致
"""

import pymysql
import sys
import os

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '2wsx1QAZaczt',
    'database': 'acwl-ai-data',
    'charset': 'utf8mb4'
}

def fix_tasktype_enum():
    """
    修复 task_type 枚举值问题
    """
    connection = None
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("开始修复 task_type 枚举值...")
        
        # 1. 查看当前枚举定义
        print("\n1. 查看当前 task_type 枚举定义:")
        cursor.execute("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'acwl_task_definitions' 
            AND COLUMN_NAME = 'task_type'
        """, (DB_CONFIG['database'],))
        
        result = cursor.fetchone()
        if result:
            print(f"当前枚举定义: {result[0]}")
        
        # 2. 查看表中实际的 task_type 值
        print("\n2. 查看表中实际的 task_type 值:")
        cursor.execute("SELECT DISTINCT task_type FROM acwl_task_definitions")
        current_values = cursor.fetchall()
        print(f"当前值: {[row[0] for row in current_values]}")
        
        # 3. 修改枚举定义为小写值（与代码中的 TaskType 枚举一致）
        print("\n3. 修改枚举定义为小写值...")
        alter_sql = """
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
            ) NOT NULL COMMENT '任务类型'
        """
        
        cursor.execute(alter_sql)
        print("枚举定义已更新为小写值")
        
        # 4. 更新所有大写值为小写值
        print("\n4. 更新所有大写值为小写值...")
        
        # 映射关系：大写 -> 小写
        value_mapping = {
            'DATA_SYNC': 'data_sync',
            'MODEL_TRAIN': 'model_train',
            'MODEL_TRAINING': 'model_train',  # 处理可能的变体
            'DATA_ANALYSIS': 'data_analysis',
            'MODEL_INFERENCE': 'model_inference',
            'DATA_PREPROCESSING': 'data_preprocessing',
            'MODEL_EVALUATION': 'model_evaluation',
            'DATA_VISUALIZATION': 'data_visualization',
            'WORKFLOW_ORCHESTRATION': 'workflow_orchestration',
            'CUSTOM': 'custom'
        }
        
        total_updated = 0
        for old_value, new_value in value_mapping.items():
            cursor.execute(
                "UPDATE acwl_task_definitions SET task_type = %s WHERE task_type = %s",
                (new_value, old_value)
            )
            updated_count = cursor.rowcount
            if updated_count > 0:
                print(f"  更新 {old_value} -> {new_value}: {updated_count} 条记录")
                total_updated += updated_count
        
        print(f"总共更新了 {total_updated} 条记录")
        
        # 5. 提交更改
        connection.commit()
        print("\n5. 更改已提交")
        
        # 6. 验证修复结果
        print("\n6. 验证修复结果:")
        
        # 查看新的枚举定义
        cursor.execute("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'acwl_task_definitions' 
            AND COLUMN_NAME = 'task_type'
        """, (DB_CONFIG['database'],))
        
        result = cursor.fetchone()
        if result:
            print(f"新的枚举定义: {result[0]}")
        
        # 查看表中的值分布
        cursor.execute("""
            SELECT task_type, COUNT(*) as count 
            FROM acwl_task_definitions 
            GROUP BY task_type 
            ORDER BY task_type
        """)
        
        value_distribution = cursor.fetchall()
        print("\n当前 task_type 值分布:")
        for value, count in value_distribution:
            print(f"  {value}: {count} 条记录")
        
        print("\n✅ task_type 枚举值修复完成！")
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        if connection:
            connection.rollback()
        sys.exit(1)
    
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    fix_tasktype_enum()