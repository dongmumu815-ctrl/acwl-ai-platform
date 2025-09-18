#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员用户的脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db_context
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin_user():
    """
    创建管理员用户
    """
    async with get_db_context() as db:
        try:
            # 检查是否已存在管理员用户
            result = await db.execute(select(User).where(User.username == "admin"))
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print(f"管理员用户已存在: {existing_admin.username} ({existing_admin.email})")
                print(f"角色: {existing_admin.role}")
                print(f"是否为管理员: {existing_admin.is_admin}")
                print(f"是否激活: {existing_admin.is_active}")
                
                # 如果不是管理员，更新为管理员
                if not existing_admin.is_admin:
                    existing_admin.is_admin = True
                    existing_admin.role = "admin"
                    await db.commit()
                    print("✅ 已将用户更新为管理员")
                else:
                    print("✅ 用户已经是管理员")
                return existing_admin
            
            # 创建新的管理员用户
            admin_user = User(
                username="admin",
                email="admin@acwl.ai",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_admin=True,
                is_active=True
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            print("✅ 管理员用户创建成功!")
            print(f"用户名: {admin_user.username}")
            print(f"邮箱: {admin_user.email}")
            print(f"密码: admin123")
            print(f"角色: {admin_user.role}")
            print(f"是否为管理员: {admin_user.is_admin}")
            
            return admin_user
            
        except Exception as e:
            print(f"❌ 创建管理员用户失败: {e}")
            await db.rollback()
            return None
        except Exception as e:
            print(f"❌ 创建管理员用户失败: {e}")
            raise

async def list_all_users():
    """
    列出所有用户
    """
    async with get_db_context() as db:
        try:
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            print(f"\n数据库中共有 {len(users)} 个用户:")
            for user in users:
                print(f"  - {user.username} ({user.email}) - 角色: {user.role} - 管理员: {user.is_admin} - 激活: {user.is_active}")
                
        except Exception as e:
            print(f"❌ 获取用户列表失败: {e}")

async def main():
    """
    主函数
    """
    print("=== 创建管理员用户 ===")
    
    # 先列出现有用户
    await list_all_users()
    
    # 创建管理员用户
    admin_user = await create_admin_user()
    
    if admin_user:
        print("\n=== 管理员用户信息 ===")
        print(f"ID: {admin_user.id}")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"角色: {admin_user.role}")
        print(f"是否为管理员: {admin_user.is_admin}")
        print(f"是否激活: {admin_user.is_active}")
        print(f"创建时间: {admin_user.created_at}")
        
        print("\n=== 登录信息 ===")
        print("用户名: admin")
        print("密码: admin123")
        print("或者")
        print("邮箱: admin@acwl.ai")
        print("密码: admin123")
    
    print("\n=== 完成 ===")

if __name__ == "__main__":
    asyncio.run(main())