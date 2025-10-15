#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单检查api_usage_logs表数据
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.log import ApiUsageLog
from sqlalchemy import text

def check_api_usage_logs():
    """
    检查api_usage_logs表的数据情况
    """
    print("\n=== 检查API使用日志表数据 ===")
    print(f"当前时间: {datetime.now()}")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 1. 检查表是否存在
        print("\n1. 检查表结构...")
        result = db.execute(text("SHOW TABLES LIKE 'api_usage_logs'"))
        table_exists = result.fetchone()
        
        if table_exists:
            print("✓ api_usage_logs表存在")
        else:
            print("✗ api_usage_logs表不存在")
            return
        
        # 2. 检查表中的记录数量
        print("\n2. 检查记录数量...")
        count = db.query(ApiUsageLog).count()
        print(f"总记录数: {count}")
        
        if count == 0:
            print("\n⚠️  表中没有数据记录")
            print("\n可能的原因:")
            print("1. 还没有进行过API调用")
            print("2. 数据保存逻辑可能有问题")
            print("3. 数据库连接或配置问题")
        else:
            # 3. 显示最近的几条记录
            print("\n3. 最近的记录:")
            recent_logs = db.query(ApiUsageLog).order_by(ApiUsageLog.created_at.desc()).limit(3).all()
            
            for i, log in enumerate(recent_logs, 1):
                print(f"\n记录 {i}:")
                print(f"  ID: {log.id}")
                print(f"  请求ID: {log.request_id}")
                print(f"  批次ID: {log.batch_id}")
                print(f"  客户ID: {log.customer_id}")
                print(f"  API ID: {log.api_id}")
                print(f"  文件路径: {log.file_path}")
                print(f"  响应状态: {log.response_status}")
                print(f"  数据大小: {log.data_size}")
                print(f"  记录数量: {log.record_count}")
                print(f"  创建时间: {log.created_at}")
        
        # 4. 检查字段结构
        print("\n4. 检查表结构...")
        result = db.execute(text("DESCRIBE api_usage_logs"))
        columns = result.fetchall()
        
        print("表字段:")
        for col in columns:
            print(f"  {col[0]} - {col[1]}")
            
    except Exception as e:
        print(f"\n❌ 检查过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    check_api_usage_logs()