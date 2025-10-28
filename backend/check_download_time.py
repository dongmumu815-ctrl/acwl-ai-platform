#!/usr/bin/env python3
"""检查资源包download_time字段数据类型的脚本"""

import asyncio
import sys
sys.path.append('.')
from app.core.database import get_db
from app.models.resource_package import ResourcePackage
from sqlalchemy import select

async def check_download_time_data():
    """检查数据库中download_time字段的数据类型"""
    async for db in get_db():
        try:
            # 查询所有资源包的download_time字段
            result = await db.execute(
                select(ResourcePackage.id, ResourcePackage.name, ResourcePackage.download_time)
                .limit(10)
            )
            packages = result.all()
            
            print('资源包download_time字段数据检查:')
            print('=' * 50)
            
            if not packages:
                print('没有找到资源包数据')
                return
            
            for pkg in packages:
                print(f'ID: {pkg.id}, Name: {pkg.name}')
                print(f'  download_time: {pkg.download_time} (type: {type(pkg.download_time)})')
                
                # 检查是否为整数类型
                if isinstance(pkg.download_time, (int, float)):
                    print(f'  ⚠️  发现问题：download_time是{type(pkg.download_time).__name__}类型，应该是datetime类型')
                elif pkg.download_time is None:
                    print(f'  ✓ download_time为None，正常')
                else:
                    print(f'  ✓ download_time类型正常')
                print()
                
        except Exception as e:
            print(f'查询失败: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(check_download_time_data())