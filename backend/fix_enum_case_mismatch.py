#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复枚举值大小写不匹配问题
将数据库中的小写枚举值更新为大写
"""

import pymysql
from app.core.config import settings


def fix_enum_case_mismatch():
    """
    修复 task_type 枚举值大小写不匹配问题
    将数据库中的小写值更新为对应的大写值
    """
    
    # 枚举值映射：小写 -> 大写
    enum_mapping = {
        'data_sync': 'DATA_SYNC',
        'model_train': 'MODEL_TRAIN', 
        'data_analysis': 'DATA_ANALYSIS',
        'model_inference': 'MODEL_INFERENCE',
        'data_preprocessing': 'DATA_PREPROCESSING',
        'model_evaluation': 'MODEL_EVALUATION',
        'data_visualization': 'DATA_VISUALIZATION',
        'workflow_orchestration': 'WORKFLOW_ORCHESTRATION',
        'custom': 'CUSTOM'
    }
    
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET
        )
        
        print(f"✅ 连接数据库成功: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        
        with connection.cursor() as cursor:
            # 1. 查看当前的枚举值分布
            print("\n📊 当前 task_type 枚举值分布:")
            cursor.execute("SELECT task_type, COUNT(*) as count FROM acwl_task_definitions GROUP BY task_type")
            current_values = cursor.fetchall()
            for value, count in current_values:
                print(f"  {value}: {count} 条记录")
            
            # 2. 先将字段类型改为VARCHAR以便更新
            print("\n🔧 临时将字段类型改为VARCHAR...")
            cursor.execute("ALTER TABLE acwl_task_definitions MODIFY COLUMN task_type VARCHAR(50) NOT NULL")
            print("✅ 字段类型临时修改成功")
            
            # 3. 更新所有小写值为大写值
            print("\n🔄 更新枚举值为大写...")
            total_updated = 0
            
            for lowercase, uppercase in enum_mapping.items():
                update_sql = "UPDATE acwl_task_definitions SET task_type = %s WHERE task_type = %s"
                cursor.execute(update_sql, (uppercase, lowercase))
                updated_count = cursor.rowcount
                if updated_count > 0:
                    print(f"  {lowercase} -> {uppercase}: {updated_count} 条记录")
                    total_updated += updated_count
            
            # 4. 恢复枚举定义为只包含大写值
            print("\n🔧 恢复枚举定义为大写值...")
            final_enum_values = "'DATA_SYNC','MODEL_TRAIN','DATA_ANALYSIS','MODEL_INFERENCE','DATA_PREPROCESSING','MODEL_EVALUATION','DATA_VISUALIZATION','WORKFLOW_ORCHESTRATION','CUSTOM'"
            
            final_alter_sql = f"ALTER TABLE acwl_task_definitions MODIFY COLUMN task_type ENUM({final_enum_values}) NOT NULL"
            cursor.execute(final_alter_sql)
            print("✅ 最终枚举定义修改成功")
            
            # 5. 验证修改结果
            print("\n📊 修改后的 task_type 枚举值分布:")
            cursor.execute("SELECT task_type, COUNT(*) as count FROM acwl_task_definitions GROUP BY task_type")
            final_values = cursor.fetchall()
            for value, count in final_values:
                print(f"  {value}: {count} 条记录")
            
            # 提交事务
            connection.commit()
            print(f"\n✅ 枚举值大小写修复完成！总共更新了 {total_updated} 条记录")
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        if 'connection' in locals():
            connection.rollback()
        raise
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("🔌 数据库连接已关闭")


if __name__ == "__main__":
    print("🚀 开始修复枚举值大小写不匹配问题...")
    fix_enum_case_mismatch()
    print("🎉 修复完成！")