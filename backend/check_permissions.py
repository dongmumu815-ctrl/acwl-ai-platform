#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户权限和资源包信息
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_async_db_session
from app.models.user import User
from app.models.resource_package import ResourcePackage, ResourcePackagePermission
from app.schemas.resource_package import PermissionType


async def check_user_and_permissions():
    """
    检查用户信息和资源包权限
    """
    print("=== 检查用户信息和资源包权限 ===\n")
    
    async with get_async_db_session() as db:
        try:
            # 查找用户ID=5的用户信息
            user_query = select(User).where(User.id == 5)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if user:
                print(f"用户信息:")
                print(f"  ID: {user.id}")
                print(f"  邮箱: {user.email}")
                print(f"  用户名: {user.username}")
                print(f"  是否激活: {user.is_active}")
                print(f"  是否管理员: {user.is_admin}")
            else:
                print("❌ 未找到用户ID=5的用户")
                return
            
            # 查找资源包ID=4的信息
            print(f"\n资源包信息:")
            package_query = select(ResourcePackage).where(ResourcePackage.id == 4)
            package_result = await db.execute(package_query)
            package = package_result.scalar_one_or_none()
            
            if package:
                print(f"  ID: {package.id}")
                print(f"  名称: {package.name}")
                print(f"  描述: {package.description}")
                print(f"  类型: {package.type}")
                print(f"  是否激活: {package.is_active}")
                print(f"  创建者ID: {package.created_by}")
                print(f"  模板ID: {package.template_id}")
                print(f"  模板类型: {package.template_type}")
            else:
                print("❌ 未找到资源包ID=4")
                return
            
            # 查找用户对资源包的权限
            print(f"\n权限信息:")
            permission_query = select(ResourcePackagePermission).where(
                and_(
                    ResourcePackagePermission.package_id == 4,
                    ResourcePackagePermission.user_id == 5
                )
            )
            permission_result = await db.execute(permission_query)
            permissions = permission_result.scalars().all()
            
            if permissions:
                for perm in permissions:
                    print(f"  权限ID: {perm.id}")
                    print(f"  权限类型: {perm.permission_type}")
                    print(f"  是否激活: {perm.is_active}")
                    print(f"  创建时间: {perm.created_at}")
                    if perm.expires_at:
                        print(f"  过期时间: {perm.expires_at}")
                    print()
            else:
                print("❌ 用户ID=5对资源包ID=4没有任何权限")
            
            # 查找所有资源包权限
            print(f"\n所有资源包权限:")
            all_permissions_query = select(ResourcePackagePermission)
            all_permissions_result = await db.execute(all_permissions_query)
            all_permissions = all_permissions_result.scalars().all()
            
            if all_permissions:
                for perm in all_permissions:
                    print(f"  资源包ID: {perm.package_id}, 用户ID: {perm.user_id}, 权限: {perm.permission_type}, 激活: {perm.is_active}")
            else:
                print("❌ 数据库中没有任何资源包权限记录")
            
            # 查找所有资源包
            print(f"\n所有资源包:")
            all_packages_query = select(ResourcePackage)
            all_packages_result = await db.execute(all_packages_query)
            all_packages = all_packages_result.scalars().all()
            
            if all_packages:
                for pkg in all_packages:
                    print(f"  ID: {pkg.id}, 名称: {pkg.name}, 创建者: {pkg.created_by}, 激活: {pkg.is_active}")
            else:
                print("❌ 数据库中没有任何资源包")
                
        except Exception as e:
            print(f"检查失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_user_and_permissions())