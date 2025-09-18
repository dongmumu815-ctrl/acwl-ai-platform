#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据资源API
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import AsyncSessionLocal
from app.services.data_resource_service import DataResourceService
from app.schemas.data_resource import DataResourceSearchRequest
from app.models.user import User
from sqlalchemy import text

async def debug_api():
    """调试数据资源API"""
    async with AsyncSessionLocal() as db:
        try:
            # 首先检查用户是否存在
            result = await db.execute(text("SELECT * FROM acwl_users WHERE id = 5"))
            user = result.first()
            if user:
                print(f"找到用户: {user}")
            else:
                print("用户ID 5不存在")
                return
            
            # 创建搜索请求
            search_request = DataResourceSearchRequest(
                keyword=None,
                category_id=None,
                resource_type=None,
                datasource_id=None,
                tags=None,
                is_public=None,
                status=None,
                created_by=None,
                sort_by="created_at",
                sort_order="desc",
                page=1,
                size=20
            )
            
            print("开始调用数据资源服务...")
            service = DataResourceService(db)
            resources, total = await service.search_resources(search_request, 5)
            
            print(f"查询成功: 找到 {total} 个资源")
            for resource in resources:
                print(f"  - {resource.name}")
                
        except Exception as e:
            print(f"调试API时出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api())