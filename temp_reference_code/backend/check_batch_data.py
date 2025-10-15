#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查批次数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.db.database import get_db
    from sqlalchemy import text
except ImportError:
    # 如果导入失败，尝试直接连接数据库
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # 数据库配置
    DATABASE_URL = "mysql+pymysql://root:123456@10.20.1.200:3306/acwl_api_system"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

def check_batch_data():
    """
    检查批次数据
    """
    db = next(get_db())
    
    try:
        # 检查批次数据条数
        result = db.execute(text("SELECT COUNT(*) as count FROM api_usage_logs WHERE batch_id = 'erp-2025-014'"))
        count = result.scalar()
        print(f"批次 erp-2025-014 的数据条数: {count}")
        
        # 检查表结构
        result = db.execute(text("DESCRIBE api_usage_logs"))
        columns = result.fetchall()
        print("\napi_usage_logs 表结构:")
        for col in columns:
            print(f"  {col[0]} - {col[1]}")
            
        # 检查是否有任何数据
        result = db.execute(text("SELECT COUNT(*) as total FROM api_usage_logs"))
        total = result.scalar()
        print(f"\napi_usage_logs 表总数据条数: {total}")
        
        if total > 0:
            # 显示前几条数据的字段
            result = db.execute(text("SELECT * FROM api_usage_logs LIMIT 3"))
            rows = result.fetchall()
            print("\n前3条数据示例:")
            for i, row in enumerate(rows):
                print(f"  第{i+1}条: {dict(row._mapping)}")
                
    except Exception as e:
        print(f"错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_batch_data()