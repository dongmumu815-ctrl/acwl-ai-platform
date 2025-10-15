#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带有batch_id的API调用

验证API调用时batch_id是否正确记录到api_usage_logs表中

Author: System
Date: 2025-07-18
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import uuid
from datetime import datetime
from app.core.database import get_db
from app.models.log import ApiUsageLog
from sqlalchemy import desc

def test_api_call_with_batch_id():
    """
    测试带有batch_id的API调用
    """
    print("🚀 测试带有batch_id的API调用...")
    print("=" * 60)
    
    # 生成测试batch_id
    test_batch_id = f"test_batch_{uuid.uuid4().hex[:8]}"
    print(f"📋 测试批次ID: {test_batch_id}")
    
    # API调用参数
    api_url = "http://localhost:8000/api/v1/custom/3/batch/" + test_batch_id
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token_customer_6"  # 使用测试token
    }
    
    # 测试数据
    test_data = {
        "data": [
            {"name": "张三", "age": 25, "city": "北京"},
            {"name": "李四", "age": 30, "city": "上海"},
            {"name": "王五", "age": 28, "city": "广州"}
        ]
    }
    
    print(f"🌐 API URL: {api_url}")
    print(f"📊 测试数据: {len(test_data['data'])} 条记录")
    
    try:
        # 发送API请求
        print(f"\n📤 发送API请求...")
        response = requests.post(api_url, headers=headers, json=test_data, timeout=30)
        
        print(f"✅ API响应状态: {response.status_code}")
        print(f"📄 响应内容: {response.text[:200]}..." if len(response.text) > 200 else f"📄 响应内容: {response.text}")
        
        # 等待一下让异步日志记录完成
        import time
        time.sleep(2)
        
        # 查询数据库中的日志记录
        print(f"\n🔍 查询数据库中的日志记录...")
        db = next(get_db())
        try:
            # 查询最新的日志记录
            latest_logs = db.query(ApiUsageLog).order_by(desc(ApiUsageLog.created_at)).limit(5).all()
            
            print(f"📊 最新的 {len(latest_logs)} 条日志记录:")
            print("-" * 60)
            
            batch_found = False
            for log in latest_logs:
                print(f"ID: {log.id}")
                print(f"API ID: {log.api_id}")
                print(f"客户ID: {log.customer_id}")
                print(f"批次ID: {log.batch_id}")
                print(f"HTTP方法: {log.http_method}")
                print(f"响应状态: {log.response_status}")
                print(f"处理时间: {log.processing_time}ms")
                print(f"创建时间: {log.created_at}")
                
                if log.batch_id == test_batch_id:
                    batch_found = True
                    print(f"🎯 找到目标批次记录！")
                
                print("-" * 40)
            
            if batch_found:
                print(f"\n✅ 测试成功！batch_id已正确记录到api_usage_logs表中")
            else:
                print(f"\n❌ 测试失败！未找到对应的batch_id记录")
                
                # 查询是否有任何包含batch_id的记录
                batch_logs = db.query(ApiUsageLog).filter(
                    ApiUsageLog.batch_id.isnot(None)
                ).order_by(desc(ApiUsageLog.created_at)).limit(3).all()
                
                if batch_logs:
                    print(f"\n📋 数据库中包含batch_id的记录:")
                    for log in batch_logs:
                        print(f"   批次ID: {log.batch_id}, 创建时间: {log.created_at}")
                else:
                    print(f"\n⚠️  数据库中暂无包含batch_id的记录")
            
        finally:
            db.close()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {str(e)}")
        print(f"💡 请确保API服务正在运行 (python main.py)")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    主函数
    """
    print("🧪 开始测试批次优化功能的API调用...")
    print("=" * 60)
    
    test_api_call_with_batch_id()
    
    print(f"\n💡 测试说明:")
    print(f"   - 测试带有batch_id的API调用")
    print(f"   - 验证batch_id是否正确记录到api_usage_logs表")
    print(f"   - 确认优化后的功能正常工作")

if __name__ == '__main__':
    main()