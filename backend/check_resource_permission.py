#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.data_resource import DataResource, DataResourcePermission
from app.models.user import User
from app.core.config import settings

async def check_resource_and_permission():
    """检查资源和权限"""
    
    # 创建数据库连接
    database_url = settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
    engine = create_async_engine(
        database_url,
        echo=True
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # 检查资源ID 20是否存在
            print("检查资源ID 20...")
            result = await session.execute(
                select(DataResource).where(DataResource.id == 20)
            )
            resource = result.scalar_one_or_none()
            
            if resource:
                print(f"✅ 资源存在: ID={resource.id}, 名称={resource.name}, 创建者={resource.created_by}")
            else:
                print("❌ 资源ID 20不存在")
                return
            
            # 查找admin用户
            print("\n查找admin用户...")
            result = await session.execute(
                select(User).where(User.email == 'admin@acwl.ai')
            )
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                print(f"✅ Admin用户存在: ID={admin_user.id}, 用户名={admin_user.username}")
            else:
                print("❌ Admin用户不存在")
                return
            
            # 检查权限
            print("\n检查权限...")
            result = await session.execute(
                select(DataResourcePermission).where(
                    DataResourcePermission.resource_id == 20
                )
            )
            permissions = result.scalars().all()
            
            if permissions:
                print(f"✅ 找到 {len(permissions)} 个权限记录:")
                for perm in permissions:
                    print(f"  用户ID: {perm.user_id}, 权限类型: {perm.permission_type}, 是否激活: {perm.is_active}")
            else:
                print("❌ 没有找到任何权限记录")
                
            # 检查admin用户是否是资源创建者
            if resource.created_by == admin_user.id:
                print(f"\n✅ Admin用户是资源创建者，应该有权限")
            else:
                print(f"\n❌ Admin用户不是资源创建者，需要显式权限")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_resource_and_permission())