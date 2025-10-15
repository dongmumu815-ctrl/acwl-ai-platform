#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查API使用日志

查看最新的API调用日志，特别是加密相关的字段
"""

from app.core.database import get_db
from app.models.api import CustomApi
from app.models.log import ApiUsageLog
from sqlalchemy.orm import Session

def check_api_logs():
    """
    检查API使用日志
    """
    db = next(get_db())
    
    try:
        # 查找test22333 API
        api = db.query(CustomApi).filter(CustomApi.api_code == 'test22333').first()
        if not api:
            print("❌ 未找到API: test22333")
            return
        
        print(f"✅ 找到API: {api.api_code} (ID: {api.id})")
        
        # 查询最新的API使用日志
        logs = db.query(ApiUsageLog).filter(
            ApiUsageLog.api_id == api.id
        ).order_by(ApiUsageLog.created_at.desc()).limit(3).all()
        
        if not logs:
            print("❌ 未找到API使用日志")
            return
        
        print(f"\n📊 最新的 {len(logs)} 条API调用日志:")
        print("=" * 80)
        
        for i, log in enumerate(logs, 1):
            print(f"\n日志 {i}:")
            print(f"  ID: {log.id}")
            print(f"  API ID: {log.api_id}")
            print(f"  客户ID: {log.customer_id}")
            print(f"  HTTP方法: {log.http_method}")
            print(f"  响应状态: {log.response_status}")
            print(f"  批次ID: {log.batch_id}")
            print(f"  创建时间: {log.created_at}")
            
            # 检查是否有is_encrypted字段
            if hasattr(log, 'is_encrypted'):
                print(f"  是否加密: {log.is_encrypted}")
            else:
                print(f"  是否加密: 字段不存在")
            
            # 加密相关字段
            print(f"  时间戳: {log.timestamp}")
            print(f"  Nonce: {log.nonce[:8] if log.nonce else None}...")
            print(f"  需要读取: {log.needread}")
            print(f"  加密数据长度: {len(log.encrypted_data) if log.encrypted_data else 0}")
            print(f"  IV长度: {len(log.iv) if log.iv else 0}")
            print(f"  签名长度: {len(log.signature) if log.signature else 0}")
            
            # 性能信息
            print(f"  处理时间: {log.processing_time}秒")
            print(f"  数据大小: {log.data_size}字节")
            print(f"  记录数: {log.record_count}")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    check_api_logs()