#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.models.data_resource import DataResource
from app.core.config import settings

async def test_update_resource():
    """测试更新资源"""
    
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
            # 查询资源
            print("查询资源ID 20...")
            result = await session.execute(
                select(DataResource).where(DataResource.id == 20)
            )
            resource = result.scalar_one_or_none()
            
            if not resource:
                print("❌ 资源不存在")
                return
                
            print(f"✅ 资源存在: {resource.name}")
            
            # 直接更新
            print("\n执行更新...")
            update_data = {
                "name": "测试更新资源名称",
                "description": "测试更新描述",
                "tags": {"test": "value"}
            }
            
            # 使用update语句
            stmt = (
                update(DataResource)
                .where(DataResource.id == 20)
                .values(**update_data)
            )
            
            await session.execute(stmt)
            await session.commit()
            
            print("✅ 更新成功")
            
            # 重新查询验证
            print("\n验证更新结果...")
            result = await session.execute(
                select(DataResource).where(DataResource.id == 20)
            )
            updated_resource = result.scalar_one_or_none()
            
            if updated_resource:
                print(f"✅ 验证成功: 名称={updated_resource.name}, 描述={updated_resource.description}")
            else:
                print("❌ 验证失败: 资源不存在")
                
        except Exception as e:
            await session.rollback()
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_update_resource())