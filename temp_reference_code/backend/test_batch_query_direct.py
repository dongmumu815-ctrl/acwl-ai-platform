#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试批次查询逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.batch import DataBatch
# 直接在脚本中定义响应模型
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BatchResponse(BaseModel):
    """批次响应模型"""
    batch_id: str = Field(..., description="批次ID")
    batch_name: Optional[str] = Field(None, description="批次名称")
    description: Optional[str] = Field(None, description="批次描述")
    status: str = Field(..., description="批次状态")
    total_count: int = Field(0, description="总数据条数")
    pending_count: int = Field(0, description="待处理数据条数")
    processing_count: int = Field(0, description="处理中数据条数")
    completed_count: int = Field(0, description="已完成数据条数")
    failed_count: int = Field(0, description="失败数据条数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class BatchListResponse(BaseModel):
    """批次列表响应模型"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[BatchResponse] = Field(..., description="批次列表")
from sqlalchemy import and_
from datetime import datetime

def test_batch_query_logic():
    """测试批次查询逻辑"""
    print("=== 直接测试批次查询逻辑 ===")
    
    try:
        # 获取数据库连接
        db = next(get_db())
        
        # 模拟接口逻辑
        page = 1
        size = 20
        
        print("1. 构建查询条件...")
        batch_query_conditions = []
        
        print("2. 执行查询...")
        if batch_query_conditions:
            batch_query = db.query(DataBatch).filter(and_(*batch_query_conditions))
        else:
            batch_query = db.query(DataBatch)
        
        print("3. 获取总数...")
        total = batch_query.count()
        print(f"   总批次数: {total}")
        
        print("4. 分页查询...")
        offset = (page - 1) * size
        batches = batch_query.order_by(DataBatch.created_at.desc()).offset(offset).limit(size).all()
        print(f"   查询到 {len(batches)} 个批次")
        
        print("5. 构建响应数据...")
        items = []
        for i, batch in enumerate(batches):
            print(f"   处理批次 {i+1}: {batch.batch_id}")
            
            # 测试 update_counts 方法
            try:
                print(f"     - 更新统计信息...")
                batch.update_counts(db)
                print(f"     - 统计信息更新成功")
            except Exception as e:
                print(f"     - 统计信息更新失败: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # 构建响应对象
            try:
                print(f"     - 构建响应对象...")
                batch_response = BatchResponse(
                    batch_id=batch.batch_id,
                    batch_name=batch.batch_name,
                    description=batch.description,
                    status=batch.status,
                    total_count=batch.total_count,
                    pending_count=batch.pending_count,
                    processing_count=batch.processing_count,
                    completed_count=batch.completed_count,
                    failed_count=batch.failed_count,
                    created_at=batch.created_at,
                    updated_at=batch.updated_at
                )
                items.append(batch_response)
                print(f"     - 响应对象构建成功")
            except Exception as e:
                print(f"     - 响应对象构建失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("6. 构建最终响应...")
        try:
            response = BatchListResponse(
                total=total,
                page=page,
                size=size,
                items=items
            )
            print(f"✅ 查询成功!")
            print(f"   总数: {response.total}")
            print(f"   页码: {response.page}")
            print(f"   页大小: {response.size}")
            print(f"   返回项目数: {len(response.items)}")
            
            for item in response.items:
                print(f"   - 批次: {item.batch_id}, 状态: {item.status}, 总数: {item.total_count}")
                
        except Exception as e:
            print(f"❌ 最终响应构建失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 关闭数据库连接
        db.close()
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_batch_query_logic()
    print("\n测试完成！")