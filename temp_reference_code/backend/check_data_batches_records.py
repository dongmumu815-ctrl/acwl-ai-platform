#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 data_batches 表中的记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.batch import DataBatch
from sqlalchemy.orm import Session

def check_data_batches_records():
    """检查 data_batches 表中的记录"""
    try:
        # 获取数据库连接
        db = next(get_db())
        
        # 查询记录总数
        total_count = db.query(DataBatch).count()
        print(f"data_batches表中的记录数量: {total_count}")
        
        if total_count > 0:
            # 查询最近的5条记录
            records = db.query(DataBatch).order_by(DataBatch.created_at.desc()).limit(5).all()
            print("\n最近的5条记录:")
            print("-" * 80)
            for record in records:
                print(f"ID: {record.id}")
                print(f"batch_id: {record.batch_id}")
                print(f"customer_id: {record.customer_id}")
                print(f"api_id: {record.api_id}")
                print(f"status: {record.status}")
                print(f"expected_count: {record.expected_count}")
                print(f"total_count: {record.total_count}")
                print(f"created_at: {record.created_at}")
                print(f"updated_at: {record.updated_at}")
                if record.metadata:
                    print(f"metadata: {record.metadata}")
                print("-" * 80)
        else:
            print("\ndata_batches表中没有记录")
            
        # 关闭数据库连接
        db.close()
        
    except Exception as e:
        print(f"检查记录时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_data_batches_records()