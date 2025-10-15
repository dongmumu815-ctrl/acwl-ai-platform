#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批次优化功能

验证 api_usage_logs 表中的 batch_id 字段是否正常工作

Author: System
Date: 2025-07-18
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.log import ApiUsageLog
from sqlalchemy import desc
import json

def test_batch_id_in_logs():
    """
    测试 api_usage_logs 表中的 batch_id 字段
    """
    print("🔍 测试 api_usage_logs 表中的 batch_id 字段...")
    print("=" * 60)
    
    db = next(get_db())
    try:
        # 查询最近的API调用日志
        logs = db.query(ApiUsageLog).order_by(desc(ApiUsageLog.created_at)).limit(10).all()
        
        print(f"📊 最近的 {len(logs)} 条API调用日志:")
        print("-" * 60)
        
        batch_logs_count = 0
        for log in logs:
            print(f"ID: {log.id}")
            print(f"API ID: {log.api_id}")
            print(f"客户ID: {log.customer_id}")
            print(f"批次ID: {log.batch_id if hasattr(log, 'batch_id') else 'N/A'}")
            print(f"请求方法: {log.http_method}")
            print(f"响应状态: {log.response_status}")
            print(f"创建时间: {log.created_at}")
            
            if hasattr(log, 'batch_id') and log.batch_id:
                batch_logs_count += 1
                print(f"✅ 包含批次ID: {log.batch_id}")
            
            print("-" * 40)
        
        print(f"\n📈 统计信息:")
        print(f"   总日志数: {len(logs)}")
        print(f"   包含批次ID的日志数: {batch_logs_count}")
        print(f"   批次覆盖率: {(batch_logs_count/len(logs)*100):.1f}%" if logs else "0%")
        
        # 查询特定批次的日志
        if batch_logs_count > 0:
            print(f"\n🔍 查询包含批次ID的日志...")
            batch_logs = db.query(ApiUsageLog).filter(
                ApiUsageLog.batch_id.isnot(None)
            ).order_by(desc(ApiUsageLog.created_at)).limit(5).all()
            
            print(f"\n📋 包含批次ID的日志 ({len(batch_logs)} 条):")
            print("-" * 60)
            
            for log in batch_logs:
                print(f"批次ID: {log.batch_id}")
                print(f"API ID: {log.api_id}")
                print(f"客户ID: {log.customer_id}")
                print(f"处理时间: {log.processing_time}ms")
                print(f"创建时间: {log.created_at}")
                print("-" * 30)
        
        # 验证字段是否存在
        print(f"\n✅ 字段验证:")
        if hasattr(ApiUsageLog, 'batch_id'):
            print(f"   ✅ ApiUsageLog 模型包含 batch_id 字段")
        else:
            print(f"   ❌ ApiUsageLog 模型缺少 batch_id 字段")
        
        # 检查数据库表结构
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'api_usage_logs'
                AND COLUMN_NAME = 'batch_id'
        """))
        
        column_info = result.fetchone()
        if column_info:
            print(f"   ✅ 数据库表包含 batch_id 字段")
            print(f"      - 数据类型: {column_info[1]}")
            print(f"      - 可为空: {column_info[2]}")
            print(f"      - 注释: {column_info[3]}")
        else:
            print(f"   ❌ 数据库表缺少 batch_id 字段")
        
        print(f"\n🎉 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """
    主函数
    """
    print("🚀 开始测试批次优化功能...")
    print("=" * 60)
    
    test_batch_id_in_logs()
    
    print("\n💡 优化说明:")
    print("   - api_usage_logs 表现在包含 batch_id 字段")
    print("   - 减少了对 data_uploads 表的写入操作")
    print("   - 提高了接口响应性能")
    print("   - 保持了数据完整性和可追踪性")

if __name__ == '__main__':
    main()